"""EDA del universo y piloto de decisión con los cortes de desarrollo de la iteración 1."""
import argparse
from pathlib import Path
import re

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analizar_representacion import analizar_representacion
from ventanas import BASE, cargar_config, cargar_precios


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


def resumir(filas, grupos):
    return filas.groupby(grupos, observed=True).agg(
        activos=("activo", "nunique"),
        fechas=("corte", "nunique"),
        operaciones=("positivo", "size"),
        positivos=("positivo", "sum"),
        proporcion_positiva=("positivo", "mean"),
        retorno_neto_medio=("retorno_neto_simulado", "mean"),
        retorno_neto_mediano=("retorno_neto_simulado", "median"),
        volatilidad_anual_media=("volatilidad_anual", "mean"),
        volatilidad_reciente_anual_media=("volatilidad_reciente", "mean"),
    )


def ejecutar(ohlc, indice, nota, destino=BASE / "eda"):
    config = cargar_config()
    inicio, fin = map(pd.Timestamp, config["bloques"]["desarrollo"])
    costo = config["costo_total_piloto"]
    ruedas = config["ruedas_de_tenencia_piloto"]
    series, calendario = cargar_precios(ohlc, config)
    cortes = pd.read_csv(indice, usecols=["activo", "corte"], parse_dates=["corte"])
    cortes = cortes.loc[cortes.corte.between(inicio, fin, inclusive="left")].copy()
    assert not cortes.duplicated(["activo", "corte"]).any()

    sectores = sectores_documentados(nota)
    assert set(series) == set(sectores) == set(cortes.activo)
    activos, operaciones = [], []
    for activo, datos in series.items():
        retornos_diarios = datos.close.pct_change(fill_method=None)
        volatilidad = retornos_diarios.std() * np.sqrt(252)
        volatilidad_reciente = retornos_diarios.rolling(20).std() * np.sqrt(252)
        activos.append({
            "activo": activo, "sector": sectores[activo], "volatilidad_anual": volatilidad,
            "ruedas_ohlc": len(datos), "ruedas_esperadas": len(calendario),
            "cobertura_ohlc": len(datos) / len(calendario),
            "primera_rueda": datos.index[0], "ultima_rueda": datos.index[-1],
        })
        for corte in cortes.loc[cortes.activo.eq(activo), "corte"].sort_values():
            pos = calendario.get_loc(corte)
            horizonte = calendario[pos:pos + ruedas + 1]
            if len(horizonte) != ruedas + 1 or not horizonte.isin(datos.index).all():
                continue
            entrada, salida = datos.loc[horizonte[[1, -1]]].itertuples()
            retorno = salida.close / entrada.open - 1 - costo
            operaciones.append({"activo": activo, "corte": corte, "entrada": entrada.Index,
                                "salida": salida.Index, "retorno_neto_simulado": retorno,
                                "positivo": retorno > 0,
                                "volatilidad_reciente": volatilidad_reciente.loc[corte]})

    universo = pd.DataFrame(activos).sort_values("volatilidad_anual")
    universo["volatilidad_grupo"] = pd.qcut(
        universo.volatilidad_anual, 3, labels=["Baja", "Media", "Alta"]
    )
    operaciones = pd.DataFrame(operaciones)
    componentes = operaciones.merge(
        universo[["activo", "sector", "volatilidad_grupo", "volatilidad_anual"]],
        on="activo", validate="many_to_one",
    )
    resumen = resumir(componentes, "activo").drop(columns=["activos", "volatilidad_anual_media"])
    universo = universo.merge(resumen, on="activo", how="left", validate="one_to_one")
    matriz = pd.crosstab(universo.sector, universo.volatilidad_grupo)
    destino.mkdir(parents=True, exist_ok=True)
    cobertura_cortes = cortes.groupby("corte").size().rename("candidatos").to_frame()
    cobertura_cortes["operaciones_con_horizonte_completo"] = (
        operaciones.groupby("corte").size().reindex(cobertura_cortes.index, fill_value=0)
    )
    cobertura_cortes["excluidos"] = (
        cobertura_cortes.candidatos - cobertura_cortes.operaciones_con_horizonte_completo
    )
    cobertura_cortes.to_csv(destino / "cortes_desarrollo.csv")
    universo.to_csv(destino / "activos_desarrollo.csv", index=False)
    operaciones.drop(columns="volatilidad_reciente").to_csv(
        destino / "operaciones_desarrollo.csv", index=False,
    )
    for grupo, archivo in [
        ("corte", "resultados_por_fecha_desarrollo.csv"),
        ("sector", "resultados_por_sector_desarrollo.csv"),
        ("volatilidad_grupo", "resultados_por_tercil_desarrollo.csv"),
        (["sector", "volatilidad_grupo"], "resultados_por_sector_y_tercil_desarrollo.csv"),
    ]:
        tabla = resumir(componentes, grupo)
        if grupo == "corte":
            tabla = tabla.drop(columns="volatilidad_anual_media")
        tabla.to_csv(destino / archivo)
    matriz.to_csv(destino / "sectores_y_volatilidad.csv")
    figura_fechas(componentes, destino, costo, ruedas)
    candidatos = analizar_representacion(series, calendario, operaciones, config, destino)

    fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
    sectores_ordenados = sorted(universo.sector.unique())
    colores = {"Baja": "#357799", "Media": "#C17821", "Alta": "#8A477D"}
    for grupo, filas in universo.groupby("volatilidad_grupo", observed=True):
        ax.scatter(filas.volatilidad_anual * 100, filas.sector.map(sectores_ordenados.index),
                   label=grupo, color=colores[grupo], alpha=.78, s=44)
    ax.set_yticks(range(len(sectores_ordenados)), sectores_ordenados)
    ultimo_anio = (fin - pd.Timedelta(days=1)).year
    ax.set(xlabel="Volatilidad anualizada (%)",
           title=f"{len(universo)} activos en desarrollo · {inicio.year}–{ultimo_anio}")
    ax.legend(title="Tercil")
    ax.grid(axis="x", alpha=.2)
    fig.savefig(destino / "sectores_y_volatilidad.png", dpi=160)
    plt.close(fig)
    print(matriz.to_string())
    print(candidatos.to_string(index=False))
    print(f"{len(operaciones)} operaciones, {operaciones.corte.nunique()} fechas, "
          f"{operaciones.positivo.sum()} positivas, "
          f"volatilidad {universo.volatilidad_anual.min():.1%}–{universo.volatilidad_anual.max():.1%}")


def figura_fechas(componentes, destino, costo, ruedas):
    por_fecha = resumir(componentes, "corte")
    fechas = por_fecha.index
    retornos = por_fecha.retorno_neto_medio * 100
    positivos = por_fecha.proporcion_positiva * 100
    vol = por_fecha.volatilidad_reciente_anual_media * 100
    fig, (ax, ax2, ax3) = plt.subplots(3, 1, figsize=(11, 7), sharex=True, layout="constrained")
    ax.bar(fechas, retornos, width=43, color=np.where(retornos >= 0, "#17765f", "#ac4141"))
    ax.axhline(0, color="#555555", linewidth=.8)
    ax.set_ylabel("Retorno neto medio (%)")
    ax2.plot(fechas, positivos, "o-", color="#357799", linewidth=1.2, markersize=4)
    ax2.axhline(50, color="#555555", linewidth=.8, linestyle=":")
    ax2.set(ylim=(0, 100), ylabel="Operaciones positivas (%)")
    ax3.plot(fechas, vol, "o-", color="#8A477D", linewidth=1.2, markersize=4)
    ax3.set(ylabel="Vol. reciente (%)", xlabel="Fecha de corte · Volatilidad anualizada de los últimos 20 retornos al cierre")
    ax3.set_xlim(pd.Timestamp(year=fechas[0].year, month=1, day=1),
                 pd.Timestamp(year=fechas[-1].year, month=12, day=31))
    ax3.xaxis.set_major_locator(mdates.YearLocator())
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    for posicion in (retornos.idxmax(), retornos.idxmin()):
        valor = retornos.loc[posicion]
        ax.annotate(f"{posicion:%d/%m/%Y}\n{valor:+.1f} %".replace(".", ","), (posicion, valor),
                    xytext=(0, 5 if valor >= 0 else -5), textcoords="offset points",
                    va="bottom" if valor >= 0 else "top", ha="center", fontsize=9)
    ax.margins(y=.32)
    for eje in (ax, ax2, ax3):
        eje.grid(axis="y", alpha=.18)
        eje.set_axisbelow(True)
    costo_texto = f"{costo:.2%}".replace(".", ",")
    fig.suptitle(f"Desarrollo · Compra simulada en t+1 · Piloto con costo {costo_texto} y salida t+{ruedas}")
    fig.savefig(destino / "resultados_por_fecha_desarrollo.png", dpi=155)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for nombre in ("ohlc", "indice", "nota"):
        parser.add_argument(nombre, type=Path)
    parser.add_argument("--salida", type=Path, default=BASE / "eda")
    args = parser.parse_args()
    ejecutar(args.ohlc, args.indice, args.nota, args.salida)
