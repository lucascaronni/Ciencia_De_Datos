"""Rasteriza las velas y mide el detalle que permite la escala fija."""

import hashlib
from io import BytesIO
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
from PIL import Image, ImageDraw, __version__ as pillow_version, features


VISTAS = ("mensual", "diaria")


def sha256(datos):
    return hashlib.sha256(datos).hexdigest()


def log_relativo(velas):
    valores = velas.to_numpy(dtype=np.float64)
    apertura, maximo, minimo, cierre = valores.T
    if (not np.isfinite(valores).all() or (valores <= 0).any()
            or (minimo > np.minimum(apertura, cierre)).any()
            or (maximo < np.maximum(apertura, cierre)).any()):
        raise ValueError("OHLC de entrada inválido")
    return 100 * np.log(valores / apertura[0])


def limites(entrenamiento, config):
    velas = np.concatenate(entrenamiento)
    metodo = config["metodo_cuantil"]
    inferior = float(np.quantile(velas[:, 2], config["cuantil_minimos"], method=metodo))
    superior = float(np.quantile(velas[:, 1], config["cuantil_maximos"], method=metodo))
    if not inferior < superior:
        raise ValueError("La escala necesita un intervalo positivo")
    return [inferior, superior]


def pixeles_por_unidad_central(config, escala):
    intervalo = config["alto"] - 1 - 2 * (config["margen"] + config["filas_por_cola"])
    return intervalo / (escala[1] - escala[0])


def filas_y(valores, config, escala):
    inferior, superior = escala
    cola = config["filas_por_cola"]
    factor = pixeles_por_unidad_central(config, escala)
    central = config["margen"] + cola + (superior - np.clip(valores, inferior, superior)) * factor
    distancia_arriba = np.maximum(valores - superior, 0) * factor
    distancia_abajo = np.maximum(inferior - valores, 0) * factor
    # Las colas son monótonas y empalman con la pendiente del tramo lineal.
    arriba = cola * (distancia_arriba / (cola + distancia_arriba))
    abajo = cola * (distancia_abajo / (cola + distancia_abajo))
    return central - arriba + abajo


def color_vela(apertura, cierre, colores):
    direccion = "sube" if cierre > apertura else "baja" if cierre < apertura else "plana"
    return colores[direccion]


def renderizar(valores, config, escala):
    ancho, alto, margen = (config[k] for k in ("ancho", "alto", "margen"))
    colores = config["colores"]
    radio = config["ancho_cuerpo"] // 2
    imagen = Image.new("RGB", (ancho, alto), colores["fondo"])
    dibujo = ImageDraw.Draw(imagen)
    centros = margen + (np.arange(len(valores)) + 0.5) * (ancho - 2 * margen) / len(valores)
    centros = np.floor(centros).astype(int)
    filas = np.floor(filas_y(valores, config, escala) + 0.5).astype(int)
    if (filas < margen).any() or (filas >= alto - margen).any():
        raise ValueError("La escala produjo una fila fuera del área de dibujo")
    for x, (apertura, _, _, cierre), (y_o, y_h, y_l, y_c) in zip(centros, valores, filas):
        color = color_vela(apertura, cierre, colores)
        dibujo.line((x, y_h, x, y_l), fill=color, width=1)
        dibujo.rectangle((x - radio, min(y_o, y_c), x + radio, max(y_o, y_c)), fill=color)
    salida = BytesIO()
    imagen.save(salida, format="PNG", compress_level=6)
    return salida.getvalue()


def porcentaje(seleccion):
    return 100 * float(seleccion.mean())


def medir(muestras, config, escala):
    valores = np.stack(muestras)
    _, maximo, minimo, _ = valores.transpose(2, 0, 1)
    inferior, superior = escala
    comprimidas = (minimo < inferior) | (maximo > superior)
    y_o, y_h, y_l, y_c = filas_y(valores, config, escala).transpose(2, 0, 1)
    borde_superior = config["margen"]
    borde_inferior = config["alto"] - 1 - borde_superior
    recortadas = (y_h < borde_superior) | (y_l > borde_inferior)
    primera_fila = np.floor(y_h + 0.5)
    ultima_fila = np.floor(y_l + 0.5)
    en_borde = (primera_fila == borde_superior) | (ultima_fila == borde_inferior)
    una_fila = np.floor(y_o + 0.5) == np.floor(y_c + 0.5)
    cuerpos = np.abs(y_o - y_c)
    mechas = np.stack((np.minimum(y_o, y_c) - y_h, y_l - np.maximum(y_o, y_c)))
    return {
        "imagenes": len(muestras),
        "velas": valores.shape[0] * valores.shape[1],
        "mechas": mechas.size,
        "imagenes_recortadas": int(recortadas.any(axis=1).sum()),
        "imagenes_recortadas_pct": porcentaje(recortadas.any(axis=1)),
        "velas_recortadas": int(recortadas.sum()),
        "velas_recortadas_pct": porcentaje(recortadas),
        "imagenes_con_compresion_pct": porcentaje(comprimidas.any(axis=1)),
        "velas_con_compresion_pct": porcentaje(comprimidas),
        "velas_en_borde_pct": porcentaje(en_borde),
        "primera_fila_con_velas": int(primera_fila.min()),
        "ultima_fila_con_velas": int(ultima_fila.max()),
        "cuerpos_lt_1px_pct": porcentaje(cuerpos < 1),
        "cuerpos_cero_pct": porcentaje(cuerpos == 0),
        "mechas_lt_1px_pct": porcentaje(mechas < 1),
        "mechas_cero_pct": porcentaje(mechas == 0),
        "mechas_superiores_lt_1px_pct": porcentaje(mechas[0] < 1),
        "mechas_inferiores_lt_1px_pct": porcentaje(mechas[1] < 1),
        "cuerpos_de_una_fila_pct": porcentaje(una_fila),
    }


def firma_render(config, escala):
    datos = dict(
        config=config, limites=escala, pillow=pillow_version,
        zlib=features.version_codec("zlib"), implementacion=sha256(Path(__file__).read_bytes()),
    )
    return sha256(json.dumps(datos, sort_keys=True).encode("ascii"))


def clave_cache(fuente, activo, corte, vista, firma, valores):
    contenido = sha256(valores.astype("<f8", copy=False).tobytes())
    return sha256(json.dumps([fuente, activo, corte, vista, firma, contenido], sort_keys=True).encode("ascii"))


def escribir_atomico(ruta, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=ruta.parent, delete=False) as archivo:
        temporal = Path(archivo.name)
        try:
            archivo.write(datos)
            archivo.close()
            temporal.replace(ruta)
        finally:
            temporal.unlink(missing_ok=True)


def png_de_entrada(valores, config, escala, ruta=None, usar_cache=True):
    if ruta is not None and usar_cache:
        try:
            return ruta.read_bytes(), True
        except FileNotFoundError:
            pass
    datos = renderizar(valores, config, escala)
    if ruta is not None:
        escribir_atomico(ruta, datos)
    return datos, False
