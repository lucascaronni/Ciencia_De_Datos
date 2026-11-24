"""Compara tres representaciones de los mismos precios ajustados de desarrollo."""
import argparse
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd

from ventanas import BASE, cargar_config, cargar_precios, extraer_ventana


CORTE = pd.Timestamp("2025-09-12")
ACTIVOS = ("KO", "UNP", "COP")
VISTAS = [(3, "meses", "3 meses cerrados"), (10, "ruedas", "10 ruedas")]


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
    ax.set_axisbelow(True)


def transformaciones(ventana):
    minimo, maximo = ventana.low.min(), ventana.high.max()
    intervalo = maximo - minimo
    normalizada = (ventana - minimo) / intervalo if intervalo else ventana - minimo
    return [
        ("Precio ajustado", "USD ajustados", ventana),
        ("Log natural", "ln(precio)", np.log(ventana)),
        ("Min–max", "0–1 por ventana", normalizada),
    ]


def figura(serie, calendario, activo, universo, destino):
    fig, ejes = plt.subplots(2, 3, figsize=(12, 6.2), layout="constrained")
    resumen = []
    for i, (n, unidad, nombre) in enumerate(VISTAS):
        ventana, fechas = extraer_ventana(serie, calendario, CORTE, n, unidad)
        if ventana is None:
            raise ValueError(f"Ventana de ejemplo incompleta: {activo}, {n} {unidad}")
        marcas = [0, len(ventana) - 1] if unidad == "ruedas" else list(range(len(ventana)))
        etiquetas = [ventana.index[j].strftime("%d/%m" if unidad == "ruedas" else "%Y-%m")
                     for j in marcas]
        for j, (escala, eje, datos) in enumerate(transformaciones(ventana)):
            ax = ejes[i, j]
            dibujar(ax, datos)
            ax.set_title(f"{nombre} · {escala}", fontsize=10)
            ax.set(xticks=marcas, xticklabels=etiquetas, ylabel=eje)
            ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
            ax.ticklabel_format(axis="y", style="plain", useOffset=False)
            if j == 2:
                ax.set_ylim(-.05, 1.05)
            o, h, l, c = datos.iloc[-1][["open", "high", "low", "close"]]
            resumen.append({
                "activo": activo, "tercil": universo.loc[activo, "volatilidad_grupo"],
                "corte": CORTE, "ventana": nombre, "escala": escala, "inicio": fechas[0],
                "fin": fechas[-1], "amplitud_ventana": datos.high.max() - datos.low.min(),
                "ultima_apertura": o, "ultimo_maximo": h, "ultimo_minimo": l, "ultimo_cierre": c,
                "cuerpo_ultimo": abs(c - o), "mecha_superior_ultima": h - max(o, c),
                "mecha_inferior_ultima": min(o, c) - l,
            })
    vol = f"{universo.loc[activo, 'volatilidad_anual']:.1%}".replace(".", ",")
    tercil = universo.loc[activo, "volatilidad_grupo"].lower()
    fig.suptitle(f"{activo} · Volatilidad anual {tercil} ({vol}) · Corte {CORTE:%d/%m/%Y}")
    fig.savefig(destino / f"escalas_{activo}.png", dpi=155)
    plt.close(fig)
    return resumen


def figura_ventanas(serie, calendario, config, destino):
    candidatos = [(n, "meses") for n in config["ventanas_mensuales_candidatas"]]
    candidatos += [(n, "ruedas") for n in config["ventanas_diarias_candidatas"]]
    fig, ax = plt.subplots(figsize=(11.5, 4.0), layout="constrained")
    for i, (n, unidad) in enumerate(candidatos):
        _, fechas = extraer_ventana(serie, calendario, CORTE, n, unidad)
        color = "#357799" if unidad == "meses" else "#17765f"
        ax.vlines(fechas, i - .16, i + .16, linewidth=1.15, color=color)
        ax.annotate(f"{fechas[0]:%d/%m}–{fechas[-1]:%d/%m}", (CORTE, i),
                    xytext=(8, 0), textcoords="offset points", va="center", fontsize=9)
    ax.axvline(CORTE.to_period("M").start_time, linestyle=":", linewidth=1.3,
               color="#92601e", label="Inicio del mes del corte")
    ax.axvline(CORTE, linestyle="--", linewidth=1.25, color="#444444", label="Corte")
    ax.set_yticks(range(len(candidatos)), [f"{n} {unidad}" for n, unidad in candidatos])
    ax.set_ylim(len(candidatos) - .45, -.55)
    inicio_mensual = (CORTE.to_period("M") - max(config["ventanas_mensuales_candidatas"])).start_time
    ax.set_xlim(inicio_mensual - pd.Timedelta(days=5), CORTE + pd.Timedelta(days=33))
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonthday=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.grid(axis="x", alpha=.17)
    ax.set_axisbelow(True)
    ax.legend(loc="lower left", frameon=False, ncols=2)
    ax.set_title(f"KO · Ruedas fuente de las cinco vistas al {CORTE:%d/%m/%Y}", loc="left", pad=10)
    fig.savefig(destino / "ventanas_KO.png", dpi=155)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ohlc", type=Path)
    parser.add_argument("--salida", type=Path, default=BASE / "eda")
    args = parser.parse_args()
    config = cargar_config()
    series, calendario = cargar_precios(args.ohlc, config)
    universo = pd.read_csv(args.salida / "activos_desarrollo.csv", index_col="activo")
    filas = []
    for activo in ACTIVOS:
        filas.extend(figura(series[activo], calendario, activo, universo, args.salida))
    pd.DataFrame(filas).to_csv(args.salida / "medidas_escalas_desarrollo.csv",
                                index=False, float_format="%.9g")
    figura_ventanas(series["KO"], calendario, config, args.salida)
