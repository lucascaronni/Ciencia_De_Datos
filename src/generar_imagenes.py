"""Genera y comprueba las entradas de las dos CNN desde el OHLC congelado."""

import argparse
import hashlib
from itertools import zip_longest
import json
from pathlib import Path

import numpy as np
import pandas as pd

from cargar_imagenes import cargar_dos_vistas, cargar_mensual, leer_png
from render_velas import (
    VISTAS, clave_cache, escribir_atomico, firma_render, limites, log_relativo,
    medir, pixeles_por_unidad_central, png_de_entrada, sha256,
)
from verificar_protocolo import construir, verificar
from revisar_ko import ID_KO, exportar_ko
from ventanas import BASE, CAMPOS, cargar_config, vistas_separadas


MANIFIESTO = BASE / "verificacion/manifiesto.csv"
ESCALAS = BASE / "config/escalas_imagenes.json"
ESPERADOS = {"entrenamiento": 2210, "configuracion": 578, "umbral": 986, "prueba_retrospectiva": 136}
CORTES_RESERVADOS = ["2026-07-14", "2026-08-13", "2026-09-14", "2026-10-13"]


def cargar_entradas(ruta, config):
    # construir comprueba el SHA-256 y reconstruye calendario y horizonte con claves, sin precios.
    reconstruido, calendario = construir(ruta, config)
    verificar(reconstruido, calendario, config)
    manifiesto = pd.read_csv(MANIFIESTO, parse_dates=[
        "mensual_inicio", "mensual_fin", "diaria_inicio", "diaria_fin", "corte", "entrada", "salida",
    ])
    pd.testing.assert_frame_equal(manifiesto, reconstruido)
    elegibles = manifiesto.loc[manifiesto.elegible]
    if elegibles.groupby("bloque").size().to_dict() != ESPERADOS:
        raise ValueError("Los casos elegibles no coinciden con el protocolo")

    datos = pd.read_csv(ruta, usecols=["activo", "fecha", *CAMPOS], parse_dates=["fecha"])
    series = {
        activo: grupo.set_index("fecha")[CAMPOS].sort_index()
        for activo, grupo in datos.groupby("activo")
    }
    return elegibles, calendario, series


def extraer(fila, serie, calendario, comparacion):
    vistas = vistas_separadas(serie.loc[:fila.corte], calendario[calendario <= fila.corte],
                             fila.corte, **comparacion)
    if vistas is None:
        raise ValueError(f"No hay dos vistas separadas para {fila.id}")
    (_, mensual), (_, diaria) = vistas
    if (mensual[0], mensual[-1], diaria[0], diaria[-1]) != (
        fila.mensual_inicio, fila.mensual_fin, fila.diaria_inicio, fila.corte,
    ):
        raise ValueError(f"Las ruedas fuente difieren del manifiesto para {fila.id}")
    return vistas


def transformar(vistas):
    return tuple(log_relativo(velas) for velas, _ in vistas)


def calibrar(filas, series, calendario, config, render):
    entrenamiento = filas.loc[filas.bloque == "entrenamiento"]
    valores = {
        fila.id: transformar(extraer(fila, series[fila.activo], calendario, config["primera_comparacion"]))
        for fila in entrenamiento.itertuples()
    }
    ids = "".join(f"{identificador}\n" for identificador in valores).encode("ascii")
    escalas = {}
    for i, vista in enumerate(VISTAS):
        escala = limites([par[i] for par in valores.values()], render)
        escalas[vista] = {
            "limites_centrales_log": escala,
            "pixeles_por_unidad_log_central": pixeles_por_unidad_central(render, escala),
        }
    ajuste = {
        "fuente": config["fuente"],
        "manifiesto_sha256": sha256(MANIFIESTO.read_bytes()),
        "render_sha256": sha256((BASE / "config/render.json").read_bytes()),
        "bloque_ajuste": "entrenamiento",
        "cantidad_ids": len(valores),
        "ids_sha256": sha256(ids),
        "escalas": escalas,
    }
    return ajuste, ids, valores


def comprobar_escala_congelada(ajuste):
    esperado = json.loads(ESCALAS.read_text())
    recalculado = dict(ajuste)
    escalas = esperado.pop("escalas")
    actuales = recalculado.pop("escalas")
    if recalculado != esperado or escalas.keys() != actuales.keys():
        raise ValueError("El registro de ajuste difiere del congelado")
    for vista in VISTAS:
        for campo in ("limites_centrales_log", "pixeles_por_unidad_log_central"):
            np.testing.assert_allclose(actuales[vista][campo], escalas[vista][campo], rtol=0, atol=1e-10)
    return {vista: datos["limites_centrales_log"] for vista, datos in escalas.items()}


def generar(filas, series, calendario, config, render, escalas, valores_entrenamiento, destino, usar_cache):
    firmas = {vista: firma_render(render, escalas[vista]) for vista in VISTAS}
    muestras = {(bloque, vista): [] for bloque in ESPERADOS for vista in VISTAS}
    registros = {}
    aciertos = 0
    for fila in filas.itertuples():
        valores = valores_entrenamiento.get(fila.id)
        if valores is None:
            valores = transformar(extraer(fila, series[fila.activo], calendario, config["primera_comparacion"]))
        registro = {"id": fila.id, "bloque": fila.bloque}
        for vista, entrada in zip(VISTAS, valores):
            muestras[fila.bloque, vista].append(entrada)
            clave = clave_cache(config["fuente"], fila.activo, fila.corte.date().isoformat(), vista,
                                firmas[vista], entrada)
            ruta = Path("cache") / vista / f"{clave}.png"
            datos, acierto = png_de_entrada(entrada, render, escalas[vista], destino / ruta, usar_cache)
            registro[f"{vista}_png"] = ruta.as_posix()
            registro[f"{vista}_sha256"] = sha256(datos)
            aciertos += acierto
        registros[fila.id] = registro
    tabla = pd.DataFrame(registros.values())
    for vista in VISTAS:
        if not tabla[f"{vista}_png"].is_unique:
            raise ValueError(f"Dos IDs apuntan a la misma ruta {vista}")
    indice = destino / "indice.csv"
    escribir_atomico(indice, tabla.to_csv(index=False).encode("utf-8"))
    metricas = [dict(bloque=bloque, vista=vista, **medir(valores, render, escalas[vista]))
                for (bloque, vista), valores in muestras.items()]
    return indice, registros, metricas, aciertos


def verificar_cargadores(filas, indice, forma):
    verificados = {}
    for bloque, esperado in ESPERADOS.items():
        grupo = filas.loc[filas.bloque == bloque]
        lista = zip_longest(grupo.id, cargar_mensual(indice, bloque, forma),
                            cargar_dos_vistas(indice, bloque, forma))
        huellas = {vista: hashlib.sha256() for vista in VISTAS}
        real = 0
        for identificador, simple, doble in lista:
            if simple is None or doble is None or identificador != simple[0] or identificador != doble[0]:
                raise ValueError(f"Cambió el orden o la cobertura de IDs en {bloque}: {identificador}")
            mensual = simple[1]
            otra_mensual, diaria = doble[1]
            if mensual.ruta != otra_mensual.ruta or mensual.sha256 != otra_mensual.sha256:
                raise ValueError(f"El PNG mensual difiere entre cargadores: {identificador}")
            for vista, entrada in zip(VISTAS, (mensual, diaria)):
                huellas[vista].update(f"{identificador},{entrada.sha256}\n".encode("ascii"))
            real += 1
        if real != esperado:
            raise ValueError(f"Recuento inesperado en {bloque}: {real}")
        cortes = grupo.corte.drop_duplicates().dt.strftime("%Y-%m-%d").tolist()
        verificados[bloque] = {
            "esperados": esperado, "reales_por_cargador": real, "cantidad_cortes": len(cortes),
            "png_mensuales_identicos": real,
            "sha256_id_y_png_en_orden": {vista: digest.hexdigest() for vista, digest in huellas.items()},
        }
        if bloque == "prueba_retrospectiva":
            if cortes != CORTES_RESERVADOS or not grupo.groupby("corte").size().eq(34).all():
                raise ValueError("Cambió la cobertura de los cortes reservados")
            verificados[bloque]["cortes"] = cortes
    return verificados


def verificar_futuro(filas, series, calendario, comparacion, render, escalas):
    identificadores = [ID_KO, f"KO_{CORTES_RESERVADOS[0]}", f"KO_{CORTES_RESERVADOS[-1]}"]
    controles = []
    for fila in filas.loc[filas.id.isin(identificadores)].itertuples():
        original = series[fila.activo]
        alterada = original.copy()
        posteriores = alterada.index > fila.corte
        alterada.loc[posteriores, CAMPOS] *= 1.37
        if not posteriores.any() or np.array_equal(alterada.loc[posteriores], original.loc[posteriores]):
            raise ValueError(f"El control no modificó precios: {fila.id}")
        huellas = []
        for serie in (original, alterada, original.loc[:fila.corte]):
            valores = transformar(extraer(fila, serie, calendario, comparacion))
            huellas.append({vista: sha256(png_de_entrada(valor, render, escalas[vista], usar_cache=False)[0])
                            for vista, valor in zip(VISTAS, valores)})
        original_hash, alterado_hash, truncado_hash = huellas
        if original_hash != alterado_hash or original_hash != truncado_hash:
            raise ValueError(f"Los píxeles dependen de precios posteriores: {fila.id}")
        controles.append(dict(id=fila.id, ruedas_posteriores_alteradas=int(posteriores.sum()),
                              factor=1.37, original=original_hash, alterado=alterado_hash,
                              truncado_al_corte=truncado_hash))
    if [control["id"] for control in controles] != identificadores:
        raise ValueError("Faltan cortes para el control de precios posteriores")
    return controles


def verificar_keras(indice, registro, forma):
    import keras
    from keras.utils import img_to_array, load_img

    for vista in VISTAS:
        ruta = indice.parent / registro[f"{vista}_png"]
        lectura = leer_png(ruta, registro[f"{vista}_sha256"], forma)
        with load_img(ruta, color_mode="rgb") as imagen:
            pixeles = img_to_array(imagen, data_format="channels_last", dtype="uint8")
        np.testing.assert_array_equal(pixeles, lectura.pixeles)
    return {"version": keras.__version__, "backend": keras.backend.backend(), "png_ko_verificados": len(VISTAS)}


def leer_config_render():
    return json.loads((BASE / "config/render.json").read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ohlc", type=Path)
    parser.add_argument("--destino", type=Path, default=BASE / "data/imagenes")
    parser.add_argument("--sin-cache", action="store_true", help="Redibuja todos los PNG de entrada")
    parser.add_argument("--verificar-keras", action="store_true", help="Comprueba los dos PNG de KO con Keras")
    args = parser.parse_args()

    config = cargar_config()
    render = leer_config_render()
    filas, calendario, series = cargar_entradas(args.ohlc, config)
    ajuste, ids, valores = calibrar(filas, series, calendario, config, render)
    escalas = comprobar_escala_congelada(ajuste)
    forma = (render["alto"], render["ancho"], 3)

    indice, registros, metricas, aciertos = generar(filas, series, calendario, config, render, escalas,
                                                    valores, args.destino, not args.sin_cache)
    bloques = verificar_cargadores(filas, indice, forma)
    futuro = verificar_futuro(filas, series, calendario, config["primera_comparacion"], render, escalas)
    for control in futuro:
        registro = registros[control["id"]]
        if any(control["original"][vista] != registro[f"{vista}_sha256"] for vista in VISTAS):
            raise ValueError(f"El lote difiere del render sin caché: {control['id']}")

    ko = next(filas.loc[filas.id == ID_KO].itertuples())
    vistas_ko = extraer(ko, series[ko.activo], calendario, config["primera_comparacion"])
    evidencia = args.destino / "verificacion"
    evidencia.mkdir(parents=True, exist_ok=True)
    detalle_ko = exportar_ko(vistas_ko, valores[ID_KO], registros[ID_KO], indice, evidencia, render)
    if detalle_ko["aperturas_ajustadas"] != {"mensual": 29.299129, "diaria": 27.756065}:
        raise ValueError("Las aperturas de KO difieren del ejemplo del protocolo")
    controles = dict(forma_rgb=forma, bloques=bloques, precios_posteriores=futuro, ejemplo=detalle_ko)
    if args.verificar_keras:
        controles["keras"] = verificar_keras(indice, registros[ID_KO], forma)
        print("Keras entregó los mismos píxeles para los dos PNG de KO")
    pd.DataFrame(metricas).to_csv(evidencia / "metricas.csv", index=False, float_format="%.8f")
    (evidencia / "ids_ajuste.txt").write_bytes(ids)
    (evidencia / "controles.json").write_text(json.dumps(controles, indent=2) + "\n")
    for bloque, resultado in bloques.items():
        print(f"{bloque}: {resultado['reales_por_cargador']}/{resultado['esperados']}")
    print(f"PNG de entrada: {2 * len(filas)} · reutilizados de caché: {aciertos}")
    print(f"Índice: {indice}\nEvidencia: {evidencia}")


if __name__ == "__main__":
    main()
