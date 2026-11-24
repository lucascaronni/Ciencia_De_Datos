"""Simulación de cartera de la iteración 2, a partir de retornos netos por ID."""

import numpy as np
import pandas as pd


CAPITAL_INICIAL = 100.0


def simular(filas, probabilidades, umbral, inicial=CAPITAL_INICIAL):
    """Las filas contienen un activo elegible por ID. Las probabilidades llevan el mismo índice de IDs."""
    ids = pd.Index(filas.id)
    if not ids.is_unique or not probabilidades.index.equals(ids):
        raise ValueError("Las probabilidades deben cubrir los IDs elegibles en orden y sin duplicados")
    p = probabilidades.to_numpy()
    retornos = filas.retorno_neto.to_numpy()
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Una probabilidad esperada está ausente o fuera de [0, 1]")
    if not np.isfinite(retornos).all():
        raise ValueError("Falta un retorno válido para valorar una operación esperada")
    if not np.isfinite(umbral) or not np.isfinite(inicial) or inicial <= 0:
        raise ValueError("Umbral o capital inicial inválidos")
    decisiones = filas.assign(compra=p >= umbral)
    capital = inicial
    por_corte = []
    salida_anterior = None
    for corte, grupo in decisiones.groupby("corte", sort=True):
        entrada, salida = grupo.entrada.min(), grupo.salida.max()
        if not corte < entrada <= salida or (salida_anterior and salida_anterior >= entrada):
            raise ValueError(f"Orden temporal incompatible con la liberación del capital: {corte}")
        elegibles = len(grupo)
        compradas = grupo.loc[grupo.compra, "retorno_neto"]
        operaciones = len(compradas)
        retorno = float(compradas.sum()) / elegibles
        asignado = capital / elegibles
        invertido = asignado * operaciones
        efectivo = asignado * (elegibles - operaciones)
        final = capital * (1 + retorno)
        por_corte.append({
            "corte": corte, "entrada": entrada, "salida": salida,
            "capital_inicial": capital, "capital_final": final,
            "elegibles": elegibles, "operaciones": operaciones,
            "exposicion": operaciones / elegibles, "capital_por_activo": asignado,
            "capital_invertido": invertido, "capital_en_efectivo": efectivo,
            "retorno_neto_corte": retorno, "retorno_neto_acumulado": final / inicial - 1,
        })
        capital = final
        salida_anterior = salida
    detalle = pd.DataFrame(por_corte)
    resumen = {
        "capital_final": capital, "capital_final_por_unidad": capital / inicial,
        "retorno_neto_acumulado": capital / inicial - 1,
        "operaciones": sum(f["operaciones"] for f in por_corte),
        "exposicion_media": sum(f["exposicion"] for f in por_corte) / len(por_corte) if por_corte else 0,
        "cortes": len(por_corte),
    }
    return resumen, detalle


def seleccionar_umbral(filas, probabilidades, candidatos):
    corridas = []
    for umbral in candidatos:
        resumen, detalle = simular(filas, probabilidades, umbral)
        corridas.append(({"umbral": umbral, **resumen,
                          "capital_por_unidad_redondeado_12": round(resumen["capital_final_por_unidad"], 12)},
                         detalle))
    elegido, por_corte = max(corridas, key=lambda r: (
        r[0]["capital_por_unidad_redondeado_12"], r[0]["umbral"]
    ))
    tabla = pd.DataFrame([{**r, "elegido": r["umbral"] == elegido["umbral"]} for r, _ in corridas])
    return elegido, tabla, por_corte
