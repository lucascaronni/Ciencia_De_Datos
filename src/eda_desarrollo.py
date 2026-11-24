"""EDA del universo y piloto de decisión con los cortes de desarrollo de la iteración 1."""
import argparse
import json
from pathlib import Path
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE = Path(__file__).resolve().parents[1]


def sectores_documentados(nota):
    sectores = {}
    leyendo = False
    for linea in nota.read_text().splitlines():
        if linea.startswith("| Sector | Activos |"):
            leyendo = True
            continue
        if leyendo and not linea.startswith("|"):
            break
        if leyendo:
            coincidencia = re.fullmatch(r"\| ([^|]+) \| ([A-Z, ]+) \|", linea)
            if coincidencia:
                sector, activos = coincidencia.groups()
                sectores.update({activo: sector for activo in activos.split(", ")})
    return sectores


def ejecutar(ohlc, indice, nota):
    config = json.loads((BASE / "config/experimento.json").read_text())
    inicio, fin = map(pd.Timestamp, config["bloques_historicos"]["desarrollo"])
    costo = config["costo_total_piloto"]
    ruedas = config["ruedas_de_tenencia_piloto"]
    precios = pd.read_csv(ohlc, parse_dates=["fecha"])
    precios = precios[precios.fecha.between(inicio, fin, inclusive="left")]
    cortes = pd.read_csv(indice, usecols=["activo", "corte", "bloque"], parse_dates=["corte"])
    cortes = cortes[cortes.bloque.eq("desarrollo")].copy()
    assert cortes.corte.between(inicio, fin, inclusive="left").all()
    assert not precios.duplicated(["activo", "fecha"]).any()
    assert not cortes.duplicated(["activo", "corte"]).any()

    sectores = sectores_documentados(nota)
    assert set(precios.activo) == set(sectores)
    activos, operaciones = [], []
    for activo, datos in precios.groupby("activo"):
        datos = datos.set_index("fecha").sort_index()
        volatilidad = datos.close.pct_change().std() * np.sqrt(252)
        activos.append({"activo": activo, "sector": sectores[activo], "volatilidad_anual": volatilidad})
        for corte in cortes.loc[cortes.activo.eq(activo), "corte"]:
            pos = datos.index.get_loc(corte)
            if pos + ruedas >= len(datos):
                continue
            entrada, salida = datos.iloc[pos + 1], datos.iloc[pos + ruedas]
            retorno = salida.close / entrada.open - 1 - costo
            operaciones.append({"activo": activo, "corte": corte, "entrada": entrada.name,
                                "salida": salida.name, "retorno_neto_simulado": retorno,
                                "positivo": retorno > 0})

    universo = pd.DataFrame(activos).sort_values("volatilidad_anual")
    universo["volatilidad_grupo"] = pd.qcut(
        universo.volatilidad_anual, 3, labels=["Baja", "Media", "Alta"]
    )
    operaciones = pd.DataFrame(operaciones)
    resumen = operaciones.groupby("activo").agg(
        operaciones=("positivo", "size"), positivos=("positivo", "sum"),
        retorno_neto_medio=("retorno_neto_simulado", "mean"),
    )
    universo = universo.merge(resumen, on="activo", validate="one_to_one")
    matriz = pd.crosstab(universo.sector, universo.volatilidad_grupo)
    destino = BASE / "eda"
    universo.to_csv(destino / "activos_desarrollo.csv", index=False)
    operaciones.to_csv(destino / "operaciones_desarrollo.csv", index=False)
    operaciones.groupby("corte").agg(
        operaciones=("positivo", "size"), positivos=("positivo", "sum"),
        proporcion_positiva=("positivo", "mean"),
        retorno_neto_medio=("retorno_neto_simulado", "mean"),
    ).to_csv(destino / "resultados_por_fecha_desarrollo.csv")
    matriz.to_csv(destino / "sectores_y_volatilidad.csv")

    candidatos = []
    for meses in config["ventanas_mensuales_candidatas"]:
        # Excluye el mes que contiene el corte, incluso si coincide con fin de mes.
        elegibles = operaciones[operaciones.corte.dt.to_period("M") - meses >= inicio.to_period("M")]
        fechas = sorted(elegibles.corte.unique())
        comienzos = [pd.Timestamp(f).to_period("M") - meses for f in fechas]
        solapes = sum(b < a + meses for a, b in zip(comienzos, comienzos[1:]))
        candidatos.append({"meses": meses, "filas": len(elegibles), "fechas": len(fechas),
                           "pares_de_fechas_con_meses_compartidos": solapes})
    pd.DataFrame(candidatos).to_csv(destino / "cobertura_mensual_desarrollo.csv", index=False)

    fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
    sectores_ordenados = sorted(universo.sector.unique())
    colores = {"Baja": "#357799", "Media": "#C17821", "Alta": "#8A477D"}
    for grupo, filas in universo.groupby("volatilidad_grupo", observed=True):
        ax.scatter(filas.volatilidad_anual * 100, filas.sector.map(sectores_ordenados.index),
                   label=grupo, color=colores[grupo], alpha=.78, s=44)
    ax.set_yticks(range(len(sectores_ordenados)), sectores_ordenados)
    ax.set(xlabel="Volatilidad anualizada (%)", title="34 activos en desarrollo · 2015–2022")
    ax.legend(title="Tercil")
    ax.grid(axis="x", alpha=.2)
    fig.savefig(destino / "sectores_y_volatilidad.png", dpi=160)
    plt.close(fig)
    print(matriz.to_string())
    print(pd.DataFrame(candidatos).to_string(index=False))
    print(f"{len(operaciones)} operaciones, {operaciones.corte.nunique()} fechas, "
          f"{operaciones.positivo.sum()} positivas, "
          f"volatilidad {universo.volatilidad_anual.min():.1%}–{universo.volatilidad_anual.max():.1%}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for nombre in ("ohlc", "indice", "nota"):
        parser.add_argument(nombre, type=Path)
    args = parser.parse_args()
    ejecutar(args.ohlc, args.indice, args.nota)
