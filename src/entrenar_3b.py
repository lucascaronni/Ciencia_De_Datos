"""Verifica entradas y entrena las CNN de la etapa 3B con presupuesto fijo."""

import argparse
import hashlib
from pathlib import Path
import platform

from cnn_modelos import (MODELOS, cargar_modelo, construir_modelo, dimensiones, keras,
                         lote_modelo, predecir, verificar_escalado)
from datos_3b import (BLOQUES, cargar_bloque, filas_elegibles, guardar_json, huella,
                      leer_json, resultados_ohlc, seleccionar_manifiesto, verificar_huella)
import jax
import numpy as np
import pandas as pd
from ventanas import BASE, cargar_config


PLAN = BASE / "config/entrenamiento_cnn.json"
INDICE = BASE / "data/imagenes/indice.csv"
DESTINO = BASE / "data/etapa_3b"
BLOQUES_PESOS = ("entrenamiento", "configuracion")


def guardar_csv(tabla, ruta):
    tabla.to_csv(ruta, index=False, float_format="%.17g")


def leer_csv(ruta):
    return pd.read_csv(ruta, float_precision="round_trip")


def metricas(filas, pred, epsilon):
    y = filas.etiqueta.to_numpy()
    recortadas = np.clip(pred, epsilon, 1 - epsilon)
    perdidas = -np.where(y == 1, np.log(recortadas), np.log1p(-recortadas))
    ll = pd.Series(perdidas).groupby(filas.corte, sort=False).mean().mean()
    positivos = int(y.sum())
    negativos = len(y) - positivos
    rangos = pd.Series(pred).rank(method="average").to_numpy()
    auc = ((rangos[y == 1].sum() - positivos * (positivos + 1) / 2)
           / (positivos * negativos)) if positivos and negativos else None
    return {
        "log_loss_por_fecha": float(ll),
        "brier": float(np.mean((pred - y) ** 2)),
        "auc_roc": float(auc) if auc is not None else None,
        "proporcion_positiva": positivos / len(y),
        "p_media": float(pred.mean()),
    }


def comprobar_plan(cfg, protocolo):
    if (cfg["semilla"] != protocolo["semilla"]
            or cfg["epocas_candidatas"] != protocolo["epocas_candidatas"]
            or cfg["epocas"] != max(cfg["epocas_candidatas"])
            or cfg["backend"] != keras.backend.backend()
            or cfg["plataforma"] != jax.default_backend()):
        raise ValueError("La corrida no coincide con el procedimiento congelado")
    render = leer_json(BASE / cfg["config_render"])
    if cfg["resolucion_rgb"] != [render["alto"], render["ancho"], 3]:
        raise ValueError("La resolución de la CNN no coincide con 3A")


def prevalidar(indice, manifiesto, forma):
    return {
        bloque: cargar_bloque(indice, manifiesto, bloque, forma, materializar=False)[1]
        for bloque in BLOQUES
    }


def ajustar(nombre, cfg, conjuntos):
    keras.utils.set_random_seed(cfg["semilla"])
    modelo = construir_modelo(nombre, cfg)
    escalado = verificar_escalado(modelo, cfg, conjuntos["entrenamiento"][0])
    parametros = modelo.count_params()
    capas = dimensiones(modelo)
    optimizador = dict(cfg["optimizador"])
    if optimizador.pop("nombre") != "Adam":
        raise ValueError("Optimizador inesperado")
    modelo.compile(optimizer=keras.optimizers.Adam(**optimizador),
                   loss=cfg["perdida"], jit_compile=True)
    imagenes, entrenamiento = conjuntos["entrenamiento"]
    y = entrenamiento.etiqueta.to_numpy(dtype=np.float32)
    azar = np.random.Generator(np.random.PCG64(cfg["semilla"]))
    historial, ordenes = [], []
    mejor, pesos, pred_elegidas = None, None, None
    for epoca in range(1, cfg["epocas"] + 1):
        ids = azar.permutation(len(y))
        ordenes.append(hashlib.sha256(ids.astype("<i8").tobytes()).hexdigest())
        for i in range(0, len(ids), cfg["lote"]):
            posiciones = ids[i:i + cfg["lote"]]
            modelo.train_on_batch(lote_modelo(nombre, imagenes, posiciones), y[posiciones])
        preds = {b: predecir(modelo, x, cfg["lote"]) for b, (x, _) in conjuntos.items()}
        medidas = {b: metricas(f, preds[b], cfg["epsilon_log_loss"])
                   for b, (_, f) in conjuntos.items()}
        candidato = epoca in cfg["epocas_candidatas"]
        valor = medidas["configuracion"]["log_loss_por_fecha"]
        historial.append({"epoca": epoca, "candidata": candidato, **medidas})
        if candidato and (mejor is None or valor < mejor[0]):
            mejor = (valor, epoca)
            pesos = modelo.get_weights()
            pred_elegidas = preds
        print(f"{nombre} época {epoca}: train {medidas['entrenamiento']['log_loss_por_fecha']:.6f} "
              f"| configuración {valor:.6f}", flush=True)
    return {
        "epoca_elegida": mejor[1], "parametros": parametros, "dimensiones": capas,
        "historial": historial, "control_escalado": escalado, "orden_lotes_sha256": ordenes,
    }, pesos, pred_elegidas


def guardar_checkpoint(destino, nombre, cfg, datos, pesos, originales, info):
    ruta = destino / "pesos" / f"{nombre}.weights.h5"
    limpio = construir_modelo(nombre, cfg)
    limpio.set_weights(pesos)
    limpio.save_weights(ruta)
    recargado = cargar_modelo(nombre, cfg, ruta)
    controles = {}
    for bloque, (imagenes, filas) in datos.items():
        persistidas = predecir(recargado, imagenes, cfg["lote"])
        ruta_pred = destino / f"probabilidades_{nombre}_{bloque}.csv"
        guardar_csv(filas[["id", "corte"]].assign(probabilidad=originales[bloque]), ruta_pred)
        guardadas = leer_csv(ruta_pred)
        if not guardadas.id.equals(filas.id):
            raise ValueError("Orden de IDs alterado en el archivo de probabilidades")
        np.testing.assert_allclose(persistidas, guardadas.probabilidad,
                                   rtol=0, atol=cfg["tolerancia_recarga"])
        controles[bloque] = {
            "sha256": huella(ruta_pred), "casos": len(filas),
            "max_error_abs": float(np.max(np.abs(persistidas - guardadas.probabilidad))),
        }
    info.update(pesos={"archivo": f"pesos/{ruta.name}", "sha256": huella(ruta)},
                probabilidades=controles)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ohlc", type=Path)
    parser.add_argument("--indice", type=Path, default=INDICE)
    parser.add_argument("--destino", type=Path, default=DESTINO)
    parser.add_argument("--solo-verificar", action="store_true")
    args = parser.parse_args()
    cfg, protocolo = leer_json(PLAN), cargar_config()
    comprobar_plan(cfg, protocolo)
    forma = tuple(cfg["resolucion_rgb"])
    manifiesto = seleccionar_manifiesto()
    sha_ohlc = verificar_huella(args.ohlc, protocolo["fuente"]["sha256"])
    controles = prevalidar(args.indice, manifiesto, forma)
    print("PNG, IDs y tensores contrastados con 3A:", {b: x["casos"] for b, x in controles.items()},
          flush=True)
    filas = pd.concat([filas_elegibles(manifiesto, b) for b in BLOQUES_PESOS], ignore_index=True)
    resultados = resultados_ohlc(args.ohlc, filas, protocolo)
    if args.solo_verificar:
        print(resultados.groupby("bloque").etiqueta.agg(["size", "sum"]).to_string())
        return
    args.destino.mkdir(parents=True, exist_ok=False)
    (args.destino / "pesos").mkdir()
    descartes = manifiesto.loc[manifiesto.elegible.eq("False")]
    guardar_csv(descartes, args.destino / "descartes.csv")
    guardar_csv(resultados, args.destino / "etiquetas_entrenamiento_configuracion.csv")
    conjuntos = {
        b: (cargar_bloque(args.indice, manifiesto, b, forma)[0],
            resultados.loc[resultados.bloque.eq(b)].reset_index(drop=True))
        for b in BLOQUES_PESOS
    }
    inicial_mensual, inicial_doble = (construir_modelo(n, cfg) for n in MODELOS)
    for capa in ("mensual_conv1", "mensual_conv2", "mensual_rasgos"):
        np.testing.assert_array_equal(inicial_mensual.get_layer(capa).get_weights()[0],
                                      inicial_doble.get_layer(capa).get_weights()[0])
    registro = {
        "entorno": {"python": platform.python_version(), "arquitectura": platform.machine(),
                    "sistema": platform.system(), "keras": keras.__version__, "jax": jax.__version__,
                    "numpy": np.__version__, "pandas": pd.__version__},
        "insumos": {"ohlc_sha256": sha_ohlc, "indice_sha256": huella(args.indice),
                    "plan_sha256": huella(PLAN), "cargadores": controles},
        "inicializacion_mensual_identica": True,
        "modelos": {},
    }
    for nombre in MODELOS:
        info, pesos, originales = ajustar(nombre, cfg, conjuntos)
        guardar_checkpoint(args.destino, nombre, cfg, conjuntos, pesos, originales, info)
        registro["modelos"][nombre] = info
    mensual, doble = (registro["modelos"][n] for n in MODELOS)
    if mensual["orden_lotes_sha256"] != doble["orden_lotes_sha256"]:
        raise ValueError("Los modelos recibieron distintos órdenes de lotes")
    guardar_json(args.destino / "checkpoints.json", registro)
    print("Ambos checkpoints seleccionados, guardados y recargados.", flush=True)


if __name__ == "__main__":
    main()
