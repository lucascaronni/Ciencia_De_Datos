"""Exporta los PNG de entrada de KO y un gráfico separado para clase."""

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd

from render_velas import VISTAS, color_vela, sha256
from ventanas import CAMPOS


ID_KO = "KO_2015-07-14"


def exportar_ko(vistas, valores, registro, indice, destino, config):
    fig, ejes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    fig.patch.set_facecolor("#F3F6FA")
    fig.subplots_adjust(left=0.085, right=0.973, top=0.73, bottom=0.22, wspace=0.10)
    fig.text(0.085, 0.93, "KO al cierre del 14 de julio de 2015", fontsize=21, weight="bold", color="#101826")
    fig.text(0.085, 0.855, "Cada vista parte de su primera apertura. La línea punteada marca 0.",
             fontsize=11, color="#36465B")
    fig.text(0.085, 0.075, "Vista ampliada para clase. Cada PNG usa una escala fija con compresión gradual en los extremos.",
             fontsize=10, color="#36465B")
    ejes[0].set_ylabel("100 × ln(P / P₀)", fontsize=11)
    colores = config["colores"]
    filas = []
    aperturas = {}
    hashes = {}
    for eje, vista, (velas, ruedas), transformadas in zip(ejes, VISTAS, vistas, valores):
        p0 = float(velas.iloc[0].open)
        aperturas[vista] = p0
        datos = (indice.parent / registro[f"{vista}_png"]).read_bytes()
        hashes[vista] = sha256(datos)
        if hashes[vista] != registro[f"{vista}_sha256"]:
            raise ValueError("El PNG de ejemplo no coincide con el lote")
        (destino / f"{ID_KO}_{vista}.png").write_bytes(datos)

        eje.set_facecolor(colores["fondo"])
        eje.axhline(0, color="#92A3B9", lw=1, linestyle=":", zorder=1)
        eje.yaxis.set_major_locator(MaxNLocator(7))
        eje.grid(axis="y", color="#2C3A4F", lw=0.6)
        eje.set_axisbelow(True)
        eje.tick_params(axis="both", length=0, pad=9, labelsize=9)
        eje.spines[:].set_visible(False)
        p0_texto = f"{p0:.6f}".replace(".", ",")
        titulo = "6 meses cerrados · entrada de ambas CNN" if vista == "mensual" else "9 ruedas · entrada adicional"
        eje.set_title(f"{titulo}\nP₀ = {p0_texto} USD", loc="left", fontsize=11, pad=12, linespacing=1.6)
        fechas = []
        for i, ((periodo, precios), log) in enumerate(zip(velas.iterrows(), transformadas)):
            apertura, maximo, minimo, cierre = log
            if vista == "mensual":
                sesiones = ruedas[ruedas.to_period("M") == periodo]
                inicio, fin = sesiones[0], sesiones[-1]
                fechas.append(f"{inicio:%d}–{fin:%d/%m}")
            else:
                inicio = fin = periodo
                fechas.append(f"{inicio:%d/%m}")
            color = color_vela(apertura, cierre, colores)
            eje.vlines(i, minimo, maximo, color=color, linewidth=1.15)
            if apertura == cierre:
                eje.hlines(apertura, i - 0.18, i + 0.18, color=color, linewidth=1.3)
            else:
                eje.bar(i, abs(cierre - apertura), bottom=min(apertura, cierre), width=0.36, color=color)
            filas.append(dict(vista=vista, inicio=inicio.date(), fin=fin.date(), apertura_base=p0,
                              **precios.to_dict(), **dict(zip((f"{c}_log" for c in CAMPOS), log))))
        eje.set_xticks(np.arange(len(velas)), fechas)
        eje.set_xlim(-0.55, len(velas) - 0.45)
        eje.set_xlabel("Ruedas de 2015 · día/mes", labelpad=10, fontsize=9)

    pd.DataFrame(filas).to_csv(destino / f"{ID_KO}_velas.csv", index=False, float_format="%.9f")
    fig.savefig(destino / f"{ID_KO}_explicado.png", dpi=145)
    plt.close(fig)
    return {"id": ID_KO, "aperturas_ajustadas": aperturas, "sha256_png": hashes}
