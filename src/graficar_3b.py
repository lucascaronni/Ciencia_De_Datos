"""Genera las curvas de 3B y copia los dos PNG reales del caso de ejemplo."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from cargar_imagenes import cargar_dos_vistas
from datos_3b import leer_json
from ventanas import BASE


DESTINO = BASE / "verificacion/etapa_3b"
INDICE = BASE / "data/imagenes/indice.csv"


def estilo(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.22)
    ax.set_axisbelow(True)


def curvas_entrenamiento(datos, destino):
    fig, ejes = plt.subplots(1, 2, figsize=(10, 4), sharey=True, layout="constrained")
    fig.suptitle("La pérdida en configuración aumenta con el entrenamiento", fontweight="bold", fontsize=15)
    for ax, (nombre, modelo) in zip(ejes, datos["modelos"].items()):
        estilo(ax)
        historial = modelo["historial"]
        epoca = [h["epoca"] for h in historial]
        configuracion = [h["configuracion"]["log_loss_por_fecha"] for h in historial]
        entrenamiento = [h["entrenamiento"]["log_loss_por_fecha"] for h in historial]
        ax.plot(epoca, entrenamiento, label="Entrenamiento", color="#227c6d", linewidth=2.2)
        ax.plot(epoca, configuracion, label="Configuración", color="#3a548b", linewidth=2.2)
        candidatas = [h["epoca"] for h in historial if h["candidata"]]
        ax.scatter(candidatas, [configuracion[i - 1] for i in candidatas], facecolors="white",
                   edgecolors="#3a548b", zorder=3, label="Época candidata")
        elegida = modelo["epoca_elegida"]
        ax.scatter([elegida], [configuracion[elegida - 1]], color="#b9561d", marker="D",
                   zorder=4, label="Checkpoint elegido")
        ax.set(xticks=epoca, xlabel="Época", title="Mensual" if nombre == "mensual" else "Mensual + diaria")
    ejes[0].set_ylabel("Log loss medio por fecha")
    ejes[1].legend(loc="lower left", frameon=False, fontsize=9)
    fig.savefig(destino / "curvas_entrenamiento.png", dpi=145)
    plt.close(fig)


def curvas_cartera(destino):
    datos = pd.read_csv(destino / "carteras_por_corte.csv", parse_dates=["corte", "salida"])
    fig, ax = plt.subplots(figsize=(10, 4.3), layout="constrained")
    estilo(ax)
    estilos = {
        "comprar_siempre": dict(label="Comprar siempre", color="#284e79", linewidth=2.3),
        "mensual": dict(label="Mensual", color="#1c745f", linewidth=0, marker="o",
                        markevery=(1, 4), markersize=4.5),
        "mensual_diaria": dict(label="Mensual + diaria", color="#b9561d", linewidth=0,
                               marker="D", markevery=(3, 4), markersize=4.5),
        "efectivo": dict(label="Efectivo", color="#626975", linewidth=1.6, linestyle="--"),
    }
    for nombre, formato in estilos.items():
        serie = datos.loc[datos.estrategia.eq(nombre)].sort_values("salida")
        fechas = [serie.corte.iloc[0], *serie.salida]
        capital = [serie.capital_inicial.iloc[0], *serie.capital_final]
        ax.plot(fechas, capital, **formato)
    ax.set_title("Los dos modelos compraron igual que la referencia", loc="left",
                 fontweight="bold", fontsize=15)
    ax.set(xlabel="Fecha de salida del corte", ylabel="Capital acumulado · inicial 100")
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
    ax.legend(loc="upper left", frameon=False, ncol=2)
    fig.savefig(destino / "curvas_cartera.png", dpi=145)
    plt.close(fig)


def copiar_par(indice, destino):
    caso = leer_json(destino / "operacion_ko.json")["id"]
    forma = (192, 192, 3)
    for identificador, par in cargar_dos_vistas(indice, "umbral", forma):
        if identificador == caso:
            for vista, entrada in zip(("mensual", "diaria"), par):
                (destino / f"{caso}_{vista}.png").write_bytes(entrada.ruta.read_bytes())
            return
    raise ValueError(f"No se encontró el par de imágenes de {caso}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publico", type=Path, default=DESTINO)
    parser.add_argument("--indice", type=Path, default=INDICE)
    args = parser.parse_args()
    curvas_entrenamiento(leer_json(args.publico / "entrenamiento.json"), args.publico)
    curvas_cartera(args.publico)
    copiar_par(args.indice, args.publico)


if __name__ == "__main__":
    main()
