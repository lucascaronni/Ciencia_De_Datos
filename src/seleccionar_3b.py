"""Congela o reproduce la regla de compra de 3B sin abrir resultados de 2026."""

import argparse
from io import StringIO
from pathlib import Path

from cartera import CAPITAL_INICIAL, seleccionar_umbral, simular
from cnn_modelos import MODELOS, cargar_modelo, predecir
from datos_3b import (BLOQUES, CONTROL_3A, MANIFIESTO, cargar_bloque, filas_elegibles,
                      guardar_json, huella, leer_json, resultados_ohlc,
                      seleccionar_manifiesto, verificar_huella)
from entrenar_3b import (BLOQUES_PESOS, DESTINO, INDICE, PLAN, comprobar_plan, guardar_csv,
                         leer_csv, metricas)
import numpy as np
import pandas as pd
from ventanas import BASE, cargar_config


CONGELADO = BASE / "config/congelado_3b.json"
PUBLICO = BASE / "verificacion/etapa_3b"
ARCHIVOS = (
    "informe/protocolo.md", "config/experimento.json", "config/entrenamiento_cnn.json",
    "config/render.json", "config/escalas_imagenes.json", "requirements-cnn.txt",
    "requirements-imagenes.txt", "src/cnn_modelos.py", "src/datos_3b.py", "src/cartera.py",
    "src/seleccionar_3b.py", "src/entrenar_3b.py", "src/cargar_imagenes.py",
    "src/render_velas.py", "src/ventanas.py", "verificacion/imagenes/ids_ajuste.txt",
)


def recargar_congelado(nombre, congelado, destino=DESTINO):
    """Valida las huellas de código, configuración y pesos antes de construir la CNN."""
    for archivo, esperado in congelado["sha256_versionados"].items():
        verificar_huella(BASE / archivo, esperado)
    plan = leer_json(PLAN)
    comprobar_plan(plan, cargar_config())
    pesos = congelado["modelos"][nombre]["pesos"]
    ruta = destino / pesos["archivo"]
    verificar_huella(ruta, pesos["sha256"])
    return cargar_modelo(nombre, plan, ruta)


def comprobar_checkpoint(destino, checkpoint, cfg, protocolo, indice):
    insumos = checkpoint["insumos"]
    verificar_huella(indice, insumos["indice_sha256"])
    verificar_huella(PLAN, insumos["plan_sha256"])
    if insumos["ohlc_sha256"] != protocolo["fuente"]["sha256"]:
        raise ValueError("Los checkpoints se ajustaron con otra fuente")
    for nombre in MODELOS:
        info = checkpoint["modelos"][nombre]
        historial = pd.DataFrame(info["historial"])
        if (historial.epoca.tolist() != list(range(1, cfg["epocas"] + 1))
                or historial.loc[historial.candidata, "epoca"].tolist() != cfg["epocas_candidatas"]):
            raise ValueError(f"Las épocas registradas de {nombre} difieren del protocolo")
        candidatos = [e for e in info["historial"] if e["candidata"]]
        mejor = min(candidatos, key=lambda e: (e["configuracion"]["log_loss_por_fecha"], e["epoca"]))
        if mejor["epoca"] != info["epoca_elegida"]:
            raise ValueError(f"El checkpoint de {nombre} no coincide con la regla de selección")
        verificar_huella(destino / info["pesos"]["archivo"], info["pesos"]["sha256"])
        for bloque in BLOQUES_PESOS:
            ruta = destino / f"probabilidades_{nombre}_{bloque}.csv"
            verificar_huella(ruta, info["probabilidades"][bloque]["sha256"])


def comprobar_pred(ruta, filas, recalculadas, tolerancia):
    guardadas = leer_csv(ruta)
    pd.testing.assert_frame_equal(guardadas[["id", "corte"]], filas[["id", "corte"]])
    np.testing.assert_allclose(recalculadas, guardadas.probabilidad, rtol=0, atol=tolerancia)
    return float(np.max(np.abs(recalculadas - guardadas.probabilidad)))


def recorrido_ko(filas, probabilidades, elegidos, curvas):
    fila = filas.loc[filas.activo.eq("KO")].iloc[0]
    esquema = {k: fila[k] for k in ("id", "corte", "entrada", "salida", "retorno_bruto",
                                    "costo_compra", "retorno_neto")}
    esquema["etiqueta"] = int(fila.etiqueta)
    esquema["modelos"] = {}
    for nombre in MODELOS:
        p, u = float(probabilidades[nombre][fila.id]), elegidos[nombre]["umbral"]
        datos_corte = curvas[nombre].set_index("corte").loc[fila.corte]
        parte = float(datos_corte.capital_por_activo)
        compra = p >= u
        esquema["modelos"][nombre] = {
            "probabilidad": p, "umbral": u, "compra": compra, "capital_asignado": parte,
            "aporte_al_capital_del_corte": parte * fila.retorno_neto if compra else 0,
            "capital_final_del_corte": float(datos_corte.capital_final),
            "capital_inicial_del_corte": float(datos_corte.capital_inicial),
            "elegibles": int(datos_corte.elegibles), "operaciones_del_corte": int(datos_corte.operaciones),
            "efectivo_del_corte": float(datos_corte.capital_en_efectivo),
        }
    return esquema


def comparar(filas, probabilidades, protocolo):
    candidatos = protocolo["umbrales"]
    if (protocolo["efectivo_por_periodo"] != 0 or len(set(candidatos)) != len(candidatos)
            or 0 not in candidatos or 1.01 not in candidatos):
        raise ValueError("El simulador requiere la grilla y tasa de efectivo del protocolo")
    tablas, curvas, elegidos = {}, {}, {}
    neutral = pd.Series(0.5, index=filas.id)
    referencias = {}
    for nombre, umbral in (("comprar_siempre", 0), ("efectivo", 1.01)):
        referencias[nombre], curvas[nombre] = simular(filas, neutral, umbral)
    for nombre in MODELOS:
        elegidos[nombre], tablas[nombre], curvas[nombre] = seleccionar_umbral(
            filas, probabilidades[nombre], candidatos
        )
        for referencia, umbral in (("comprar_siempre", 0), ("efectivo", 1.01)):
            corrida = tablas[nombre].loc[tablas[nombre].umbral.eq(umbral)].iloc[0]
            if not all(corrida[k] == v for k, v in referencias[referencia].items()):
                raise ValueError(f"La estrategia de referencia {referencia} difiere entre modelos")
    orden = [*MODELOS, *referencias]
    resumenes = {**elegidos, **referencias}
    resumen = pd.DataFrame([{"estrategia": n, **resumenes[n]} for n in orden]).drop(
        columns=["umbral", "capital_por_unidad_redondeado_12"]
    )
    detalle = pd.concat([curvas[n].assign(estrategia=n) for n in orden], ignore_index=True)
    grilla = pd.concat([tablas[n].assign(modelo=n) for n in MODELOS], ignore_index=True)
    for nombre in orden:
        trayecto = curvas[nombre]
        np.testing.assert_allclose(trayecto.capital_invertido + trayecto.capital_en_efectivo,
                                   trayecto.capital_inicial, rtol=0, atol=1e-12)
        np.testing.assert_allclose(np.prod(1 + trayecto.retorno_neto_corte),
                                   resumenes[nombre]["capital_final_por_unidad"], rtol=0, atol=1e-12)
    return elegidos, curvas, {
        "seleccion_umbral.csv": grilla, "carteras_por_corte.csv": detalle, "carteras_resumen.csv": resumen,
    }


def reproducir(args, cfg, protocolo, checkpoint, manifiesto, congelado):
    """Confirma la igualdad de probabilidades, tablas, métricas y umbrales en una recarga nueva."""
    verificar_huella(args.destino / "checkpoints.json", congelado["checkpoints_sha256"])
    verificar_huella(args.ohlc, congelado["ohlc_sha256"])
    verificar_huella(args.indice, congelado["indice_sha256"])
    modelos = {n: recargar_congelado(n, congelado, args.destino) for n in MODELOS}
    probabilidades = {}
    for bloque in BLOQUES:
        filas = filas_elegibles(manifiesto, bloque)
        imagenes, _ = cargar_bloque(args.indice, manifiesto, bloque, tuple(cfg["resolucion_rgb"]))
        for nombre, modelo in modelos.items():
            ruta = args.destino / f"probabilidades_{nombre}_{bloque}.csv"
            esperado = congelado["modelos"][nombre]["probabilidades"][bloque]["sha256"]
            verificar_huella(ruta, esperado)
            recalculadas = predecir(modelo, imagenes, cfg["lote"])
            error = comprobar_pred(ruta, filas, recalculadas, cfg["tolerancia_recarga"])
            print(f"Recarga {nombre}/{bloque}: error máximo {error:.2g}", flush=True)
            if bloque == "umbral":
                guardadas = leer_csv(ruta).probabilidad.to_numpy()
                for umbral in protocolo["umbrales"]:
                    np.testing.assert_array_equal(recalculadas >= umbral, guardadas >= umbral)
                probabilidades[nombre] = pd.Series(guardadas, index=filas.id)
        del imagenes
    filas = resultados_ohlc(args.ohlc, filas_elegibles(manifiesto, "umbral"), protocolo)
    verificar_huella(args.destino / "etiquetas_umbral.csv", congelado["etiquetas_umbral_sha256"])
    verificar_huella(args.destino / "etiquetas_entrenamiento_configuracion.csv",
                    congelado["etiquetas_entrenamiento_configuracion_sha256"])
    verificar_huella(args.destino / "descartes.csv", congelado["descartes_sha256"])
    elegidos, curvas, tablas = comparar(filas, probabilidades, protocolo)
    for nombre, elegido in elegidos.items():
        if elegido["umbral"] != congelado["modelos"][nombre]["umbral"]:
            raise ValueError(f"Cambió el umbral reproducido de {nombre}")
    for archivo, tabla in tablas.items():
        verificar_huella(args.publico / archivo, congelado["tablas_sha256"][archivo])
        csv = StringIO()
        guardar_csv(tabla, csv)
        if (args.publico / archivo).read_bytes() != csv.getvalue().encode("utf-8"):
            raise ValueError(f"Cambió la tabla reproducida: {archivo}")
    resumen = resumen_metricas(filas, probabilidades, checkpoint, cfg)
    if resumen != leer_json(args.publico / "prediccion.json"):
        raise ValueError("Las métricas predictivas guardadas difieren de la reproducción")
    if recorrido_ko(filas, probabilidades, elegidos, curvas) != leer_json(args.publico / "operacion_ko.json"):
        raise ValueError("El recorrido de KO difiere de la reproducción")
    entrenamiento = leer_json(args.publico / "entrenamiento.json")
    for nombre in MODELOS:
        checkpoint["modelos"][nombre]["probabilidades"]["umbral"] = (
            congelado["modelos"][nombre]["probabilidades"]["umbral"]
        )
    if entrenamiento != checkpoint:
        raise ValueError("El historial público difiere del registro local del entrenamiento")
    print("Reproducidos los dos umbrales, las carteras y las probabilidades guardadas.", flush=True)


def resumen_metricas(filas, probabilidades, checkpoint, cfg):
    resumen = {}
    for nombre, p in probabilidades.items():
        info = checkpoint["modelos"][nombre]
        epoca = info["epoca_elegida"]
        seleccionado = info["historial"][epoca - 1]
        resumen[nombre] = {b: seleccionado[b] for b in BLOQUES_PESOS}
        resumen[nombre]["umbral"] = metricas(filas, p.to_numpy(), cfg["epsilon_log_loss"])
    return resumen


def congelar(args, cfg, protocolo, checkpoint, manifiesto):
    if args.congelado.exists() or args.publico.exists() or (args.destino / "etiquetas_umbral.csv").exists():
        raise FileExistsError("La selección ya tiene artefactos; para reproducirla use --verificar")
    forma = tuple(cfg["resolucion_rgb"])
    filas = filas_elegibles(manifiesto, "umbral")
    imagenes, control = cargar_bloque(args.indice, manifiesto, "umbral", forma)
    if control != checkpoint["insumos"]["cargadores"]["umbral"]:
        raise ValueError("El bloque de umbral cambió desde la verificación inicial")
    probabilidades = {}
    modelos = checkpoint["modelos"]
    for nombre in MODELOS:
        info = modelos[nombre]
        ruta = args.destino / info["pesos"]["archivo"]
        modelo = cargar_modelo(nombre, cfg, ruta)
        p = predecir(modelo, imagenes, cfg["lote"])
        ruta_pred = args.destino / f"probabilidades_{nombre}_umbral.csv"
        guardar_csv(filas[["id", "corte"]].assign(probabilidad=p), ruta_pred)
        recargado = cargar_modelo(nombre, cfg, ruta)
        error = comprobar_pred(ruta_pred, filas, predecir(recargado, imagenes, cfg["lote"]),
                                cfg["tolerancia_recarga"])
        probabilidades[nombre] = pd.Series(p, index=filas.id)
        info["probabilidades"]["umbral"] = {"sha256": huella(ruta_pred), "casos": len(filas),
                                            "max_error_abs": error}
    filas = resultados_ohlc(args.ohlc, filas, protocolo)
    guardar_csv(filas, args.destino / "etiquetas_umbral.csv")
    elegidos, curvas, tablas = comparar(filas, probabilidades, protocolo)
    args.publico.mkdir(parents=True, exist_ok=False)
    for archivo, tabla in tablas.items():
        guardar_csv(tabla, args.publico / archivo)
    guardar_json(args.publico / "entrenamiento.json", checkpoint)
    guardar_json(args.publico / "prediccion.json", resumen_metricas(filas, probabilidades, checkpoint, cfg))
    guardar_json(args.publico / "operacion_ko.json", recorrido_ko(filas, probabilidades, elegidos, curvas))
    congelado = {
        "generador_commit": cfg["generador_commit"],
        "ohlc_sha256": protocolo["fuente"]["sha256"],
        "manifiesto": str(MANIFIESTO.relative_to(BASE)),
        "indice_local": str(INDICE.relative_to(BASE)),
        "indice_sha256": huella(args.indice),
        "pesos_y_probabilidades_locales": str(DESTINO.relative_to(BASE)),
        "checkpoints_sha256": huella(args.destino / "checkpoints.json"),
        "etiquetas_entrenamiento_configuracion_sha256": huella(
            args.destino / "etiquetas_entrenamiento_configuracion.csv"
        ),
        "etiquetas_umbral_sha256": huella(args.destino / "etiquetas_umbral.csv"),
        "descartes_sha256": huella(args.destino / "descartes.csv"),
        "sha256_versionados": {archivo: huella(BASE / archivo) for archivo in (
            *ARCHIVOS, str(MANIFIESTO.relative_to(BASE)), str(CONTROL_3A.relative_to(BASE))
        )},
        "tablas_sha256": {archivo: huella(args.publico / archivo) for archivo in tablas},
        "regla": {
            "compra": "p >= umbral", "grilla": protocolo["umbrales"],
            "criterio": "Máximo capital final por unidad inicial redondeado a 12 decimales",
            "desempate": "Umbral mayor", "capital_inicial": CAPITAL_INICIAL,
            "costo_total_compra": protocolo["costo_total_piloto"],
            "efectivo_por_periodo": protocolo["efectivo_por_periodo"],
        },
        "modelos": {n: {
            "epoca": modelos[n]["epoca_elegida"], "parametros": modelos[n]["parametros"],
            "pesos": modelos[n]["pesos"], "probabilidades": modelos[n]["probabilidades"],
            "umbral": elegidos[n]["umbral"],
        } for n in MODELOS},
    }
    guardar_json(args.congelado, congelado)
    for n, r in elegidos.items():
        print(f"{n}: umbral {r['umbral']:g}, retorno neto {r['retorno_neto_acumulado']:.4%}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ohlc", type=Path)
    parser.add_argument("--indice", type=Path, default=INDICE)
    parser.add_argument("--destino", type=Path, default=DESTINO)
    parser.add_argument("--publico", type=Path, default=PUBLICO)
    parser.add_argument("--congelado", type=Path, default=CONGELADO)
    parser.add_argument("--verificar", action="store_true")
    args = parser.parse_args()
    cfg, protocolo = leer_json(PLAN), cargar_config()
    comprobar_plan(cfg, protocolo)
    checkpoints = leer_json(args.destino / "checkpoints.json")
    comprobar_checkpoint(args.destino, checkpoints, cfg, protocolo, args.indice)
    manifiesto = seleccionar_manifiesto()
    if args.verificar:
        reproducir(args, cfg, protocolo, checkpoints, manifiesto, leer_json(args.congelado))
    else:
        congelar(args, cfg, protocolo, checkpoints, manifiesto)


if __name__ == "__main__":
    main()
