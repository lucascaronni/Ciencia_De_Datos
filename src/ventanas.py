"""Vistas candidatas construidas exclusivamente con ruedas de desarrollo."""
from pathlib import Path
import json

import numpy as np
import pandas as pd


BASE = Path(__file__).resolve().parents[1]
CAMPOS = ["open", "high", "low", "close"]
AGREGACION = {"open": "first", "high": "max", "low": "min", "close": "last"}


def cargar_config():
    return json.loads((BASE / "config/experimento.json").read_text())


def cargar_precios(ohlc, config):
    inicio, fin = map(pd.Timestamp, config["bloques"]["desarrollo"])
    datos = pd.read_csv(ohlc, parse_dates=["fecha"], usecols=["activo", "fecha", *CAMPOS])
    datos = datos.loc[datos.fecha.between(inicio, fin, inclusive="left")].copy()
    niveles = datos[CAMPOS].to_numpy()
    if (datos.empty or datos.duplicated(["activo", "fecha"]).any()
            or not np.isfinite(niveles).all() or (niveles <= 0).any()
            or (datos.low > datos[["open", "close"]].min(axis=1)).any()
            or (datos.high < datos[["open", "close"]].max(axis=1)).any()):
        raise ValueError("OHLC de desarrollo vacío, duplicado o inválido")
    calendario = pd.DatetimeIndex(datos.fecha.unique()).sort_values()
    series = {
        activo: filas.set_index("fecha")[CAMPOS].sort_index()
        for activo, filas in datos.groupby("activo")
    }
    return series, calendario


def extraer_ventana(serie, calendario, corte, cantidad, unidad):
    """Devuelve las velas y sus ruedas fuente. Exige la ventana completa."""
    if unidad == "meses":
        fin = corte.to_period("M")
        periodos = pd.period_range(end=fin - 1, periods=cantidad, freq="M")
        meses_calendario = calendario.to_period("M")
        fechas = calendario[meses_calendario.isin(periodos)]
        if not fechas.to_period("M").unique().equals(periodos):
            return None, fechas[:0]
    elif unidad == "ruedas":
        fechas = calendario[calendario <= corte][-cantidad:]
        if len(fechas) != cantidad or fechas[-1] != corte:
            return None, fechas[:0]
    else:
        raise ValueError(f"Unidad de ventana desconocida: {unidad}")

    if not fechas.isin(serie.index).all():
        return None, fechas[:0]
    velas = serie.loc[fechas]
    if unidad == "meses":
        velas = velas.groupby(velas.index.to_period("M")).agg(AGREGACION)
    return velas, fechas
