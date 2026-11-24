"""Cargadores de entradas RGB, en el orden del manifiesto y por bloque."""

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

from render_velas import sha256


@dataclass(frozen=True)
class EntradaPNG:
    ruta: Path
    sha256: str
    pixeles: np.ndarray


def filas_del_bloque(indice, bloque):
    tabla = pd.read_csv(indice, dtype=str, keep_default_na=False)
    if not tabla.id.is_unique:
        raise ValueError("El índice de imágenes contiene IDs duplicados")
    filas = tabla.loc[tabla.bloque == bloque]
    if filas.empty:
        raise ValueError(f"Bloque ausente en el índice: {bloque}")
    return filas.itertuples(index=False)


def leer_png(ruta, hash_esperado, forma):
    datos = ruta.read_bytes()
    huella = sha256(datos)
    if huella != hash_esperado:
        raise ValueError(f"El PNG no coincide con el índice: {ruta}")
    with Image.open(BytesIO(datos)) as imagen:
        if (imagen.format, imagen.mode, imagen.size) != ("PNG", "RGB", (forma[1], forma[0])):
            raise ValueError(f"Formato de entrada inesperado: {ruta}")
        pixeles = np.array(imagen, dtype=np.uint8)
    return EntradaPNG(ruta, huella, pixeles)


def cargar_mensual(indice, bloque, forma):
    """Emite pares (ID, entrada mensual). EntradaPNG.pixeles es H × W × 3."""
    for fila in filas_del_bloque(indice, bloque):
        yield fila.id, leer_png(indice.parent / fila.mensual_png, fila.mensual_sha256, forma)


def cargar_dos_vistas(indice, bloque, forma):
    """Emite pares (ID, (entrada mensual, entrada diaria)) con el mismo orden."""
    for fila in filas_del_bloque(indice, bloque):
        mensual = leer_png(indice.parent / fila.mensual_png, fila.mensual_sha256, forma)
        diaria = leer_png(indice.parent / fila.diaria_png, fila.diaria_sha256, forma)
        yield fila.id, (mensual, diaria)
