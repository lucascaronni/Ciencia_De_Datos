"""CNN de 3B y recarga de pesos sin optimizador."""

import os

os.environ.setdefault("KERAS_BACKEND", "jax")
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import keras
from keras import layers
import numpy as np


MODELOS = ("mensual", "mensual_diaria")


def rama(entrada, vista, cfg):
    plan = cfg["ramas"][vista]
    esc = cfg["escalado_pixeles"]
    x = layers.Rescaling(1 / esc["divisor"], offset=esc["offset"],
                         name=f"{vista}_escala")(entrada)
    for i, (filtros, pool, semilla) in enumerate(
        zip(plan["filtros"], plan["pool"], plan["semillas_glorot"]), 1
    ):
        x = layers.Conv2D(
            filtros, plan["kernel"], strides=plan["stride_primera_conv"] if i == 1 else 1,
            padding="same", activation="relu", name=f"{vista}_conv{i}",
            kernel_initializer=keras.initializers.GlorotUniform(seed=semilla),
        )(x)
        x = layers.MaxPooling2D(pool, name=f"{vista}_pool{i}")(x)
    x = layers.Flatten(name=f"{vista}_aplanar")(x)
    return layers.Dense(
        plan["rasgos"], activation="relu", name=f"{vista}_rasgos",
        kernel_initializer=keras.initializers.GlorotUniform(seed=plan["semillas_glorot"][-1]),
    )(x)


def construir_modelo(nombre, cfg):
    if nombre not in MODELOS:
        raise ValueError(f"CNN desconocida: {nombre}")
    keras.mixed_precision.set_global_policy(cfg["precision"])
    forma = tuple(cfg["resolucion_rgb"])
    mensual = keras.Input(forma, dtype="uint8", name="mensual")
    entradas = mensual
    rasgos = rama(mensual, "mensual", cfg)
    if nombre == "mensual_diaria":
        diaria = keras.Input(forma, dtype="uint8", name="diaria")
        entradas = [mensual, diaria]
        rasgos = layers.Concatenate(name="fusion")([rasgos, rama(diaria, "diaria", cfg)])
    esc = cfg["salida"]
    probabilidad = layers.Dense(
        1, activation=esc["activacion"], name="probabilidad",
        kernel_initializer=keras.initializers.GlorotUniform(seed=esc["semilla_glorot"]),
    )(rasgos)
    return keras.Model(entradas, probabilidad, name=nombre)


def cargar_modelo(nombre, cfg, ruta):
    modelo = construir_modelo(nombre, cfg)
    modelo.load_weights(ruta)
    return modelo


def lote_modelo(nombre, imagenes, posiciones):
    mensual = imagenes[0][posiciones]
    return mensual if nombre == "mensual" else [mensual, imagenes[1][posiciones]]


def predecir(modelo, imagenes, lote):
    n = len(imagenes[0])
    probabilidades = np.concatenate([
        np.asarray(modelo(lote_modelo(modelo.name, imagenes, slice(i, i + lote)),
                          training=False)).reshape(-1)
        for i in range(0, n, lote)
    ]).astype(np.float64)
    if probabilidades.shape != (n,) or not np.isfinite(probabilidades).all() or (
        (probabilidades < 0) | (probabilidades > 1)
    ).any():
        raise ValueError(f"Probabilidades inválidas para {modelo.name}")
    return probabilidades


def verificar_escalado(modelo, cfg, imagenes):
    esc = cfg["escalado_pixeles"]
    registros = {}
    for idx, entrada in enumerate(modelo.inputs):
        vista = entrada.name
        imagen = imagenes[idx]
        capa = modelo.get_layer(f"{vista}_escala")
        primera_conv = modelo.get_layer(f"{vista}_conv1")
        inspeccion = keras.Model(modelo.inputs[idx], [capa.output, primera_conv.input])
        prueba = np.stack([imagen[0], np.full_like(imagen[0], 255), np.zeros_like(imagen[0])])
        escalado, entrada_conv = map(np.asarray, inspeccion(prueba))
        esperado = prueba.astype(np.float32) / esc["divisor"] + esc["offset"]
        np.testing.assert_allclose(escalado, esperado, rtol=0, atol=1e-7)
        np.testing.assert_array_equal(entrada_conv, escalado)
        registros[vista] = {
            "dtype_crudo": str(prueba.dtype), "dtype_conv1": str(entrada_conv.dtype),
            "max_error_abs": float(np.max(np.abs(escalado - esperado))),
            "prueba_negro": float(entrada_conv[2, 0, 0, 0]),
            "prueba_blanco": float(entrada_conv[1, 0, 0, 0]),
        }
    if sum(isinstance(capa, layers.Rescaling) for capa in modelo.layers) != len(registros):
        raise ValueError("Cantidad inesperada de escalados de píxeles")
    return registros


def dimensiones(modelo):
    return [
        {"capa": capa.name, "tipo": type(capa).__name__,
         "salida_sin_lote": list(capa.output.shape[1:]), "parametros": capa.count_params()}
        for capa in modelo.layers
    ]
