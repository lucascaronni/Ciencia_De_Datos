"""Compara tres representaciones de los mismos precios ajustados de desarrollo."""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd


CAMPOS = ["open", "high", "low", "close"]
CORTE = pd.Timestamp("2022-09-16")
ACTIVOS = ("KO", "UNP", "COP")


def dibujar(ax, datos):
    for posicion, vela in enumerate(datos.itertuples()):
        color = "#17765f" if vela.close >= vela.open else "#ac4141"
        ax.vlines(posicion, vela.low, vela.high, color=color, linewidth=1.3)
        cuerpo = abs(vela.close - vela.open)
        if cuerpo:
            ax.add_patch(Rectangle((posicion - .28, min(vela.open, vela.close)),
                                   .56, cuerpo, color=color))
        else:
            ax.hlines(vela.close, posicion - .28, posicion + .28, color=color)
    ax.set_xlim(-.65, len(datos) - .35)
    ax.autoscale_view()
    ax.grid(axis="y", alpha=.18)


def figura(serie, activo, salida):
    primero_mes = CORTE.to_period("M").start_time
    ultimos_meses = serie.loc[(serie.index < primero_mes) &
                             (serie.index >= primero_mes - pd.DateOffset(months=3))]
    mensual = ultimos_meses.groupby(ultimos_meses.index.to_period("M")).agg(
        open=("open", "first"), high=("high", "max"),
        low=("low", "min"), close=("close", "last"),
    )
    diaria = serie.loc[:CORTE, CAMPOS].tail(10)
    assert len(mensual) == 3 and len(diaria) == 10 and diaria.index[-1] == CORTE
    fig, ejes = plt.subplots(2, 3, figsize=(11, 5.8), layout="constrained")
    for i, (ventana, nombre) in enumerate(((mensual, "3 meses cerrados"), (diaria, "10 ruedas"))):
        minimo, maximo = ventana.low.min(), ventana.high.max()
        vistas = (ventana, np.log(ventana), (ventana - minimo) / (maximo - minimo))
        marcas = [0, len(ventana) - 1] if i else list(range(len(ventana)))
        etiquetas = [(ventana.index[j].strftime("%d/%m") if i
                      else str(ventana.index[j])) for j in marcas]
        for j, (datos, titulo) in enumerate(zip(vistas, ("Precio ajustado", "Log natural", "Min–max"))):
            ax = ejes[i, j]
            dibujar(ax, datos)
            ax.set_title(titulo)
            ax.set_xticks(marcas, etiquetas)
            if j == 2:
                ax.set_ylim(-.04, 1.04)
            if j == 0:
                ax.set_ylabel(nombre)
    fig.suptitle(f"{activo} · Corte {CORTE:%d/%m/%Y} · Mismas velas en las tres columnas")
    fig.savefig(salida, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ohlc", type=Path)
    args = parser.parse_args()
    datos = pd.read_csv(args.ohlc, parse_dates=["fecha"])
    datos = datos[datos.activo.isin(ACTIVOS) & datos.fecha.le(CORTE)]
    carpeta = Path(__file__).resolve().parents[1] / "eda"
    for activo, serie in datos.groupby("activo"):
        figura(serie.set_index("fecha").sort_index(), activo, carpeta / f"escalas_{activo}.png")
