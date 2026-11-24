"""Reproduce el inventario sin leer columnas de precios ni etiquetas de prueba."""

import argparse
import hashlib
from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from ventanas import BASE, CAMPOS, cargar_config, vistas_separadas


def construir(ruta, cfg):
    if hashlib.sha256(ruta.read_bytes()).hexdigest() != cfg["fuente"]["sha256"]:
        raise ValueError("El archivo difiere del OHLC congelado")
    claves = pd.read_csv(ruta, usecols=["activo", "fecha"], parse_dates=["fecha"])
    fechas = pd.DatetimeIndex(sorted(claves.fecha.unique()))
    universo = sorted(
        pd.read_csv(BASE / "eda/activos_desarrollo.csv", usecols=["activo"]).activo
    )
    sesiones = {a: set(g.fecha) for a, g in claves.groupby("activo")}
    assert sorted(sesiones) == universo and not claves.duplicated().any()
    assert len(fechas) == 2985 and all(len(s) == len(fechas) for s in sesiones.values())
    meses = fechas.to_period("M")
    m, d = (cfg["primera_comparacion"][k] for k in ("meses", "ruedas"))
    h = cfg["ruedas_de_tenencia_piloto"]
    anterior = -h
    filas = []
    for mes in meses.unique():
        primero = meses.searchsorted(mes)
        i = max(primero + d - 1, anterior + h)
        if i >= len(fechas) or meses[i] != mes:
            continue
        # Fijar la grilla al primer mes con contexto completo, como en el EDA.
        if mes - m < meses[0]:
            continue
        anterior = i
        t = fechas[i]
        mensual = fechas[(meses >= mes - m) & (meses < mes)]
        diaria = fechas[i - d + 1 : i + 1]
        horizonte = fechas[i + 1 : i + h + 1]
        entrada = horizonte[0] if len(horizonte) else pd.NaT
        salida = horizonte[-1] if len(horizonte) == h else pd.NaT
        bloque, (inicio, fin) = next(
            (b, limites)
            for b, limites in cfg["particiones"].items()
            if pd.Timestamp(limites[0]) <= t < pd.Timestamp(limites[1])
        )
        assert len(mensual.to_period("M").unique()) == m and len(diaria) == d
        assert mensual[-1] < diaria[0] and diaria[-1] == t
        for a in universo:
            motivo = "elegible"
            if cfg["historia_dentro_del_bloque"] and mensual[0] < pd.Timestamp(inicio):
                motivo = "historia_anterior"
            elif pd.isna(salida):
                motivo = "sin_salida_en_fuente"
            elif salida >= pd.Timestamp(fin):
                motivo = "salida_en_otro_bloque"
            elif not sesiones[a].issuperset(mensual.union(diaria).union(horizonte)):
                motivo = "cobertura_incompleta"
            filas.append(
                dict(
                    id=f"{a}_{t.date()}",
                    activo=a,
                    bloque=bloque,
                    mensual_inicio=mensual[0],
                    mensual_fin=mensual[-1],
                    diaria_inicio=diaria[0],
                    diaria_fin=t,
                    corte=t,
                    entrada=entrada,
                    salida=salida,
                    elegible=motivo == "elegible",
                    motivo=motivo,
                )
            )
    return pd.DataFrame(filas), fechas


def verificar(tabla, fechas, cfg):
    ok = tabla[tabla.elegible]
    assert tabla.id.is_unique and tabla.groupby("corte").bloque.nunique().eq(1).all()
    assert (
        ok.diaria_fin.eq(ok.corte).all() and (ok.mensual_fin < ok.diaria_inicio).all()
    )
    h = cfg["ruedas_de_tenencia_piloto"]
    pos = fechas.get_indexer(ok.corte)
    assert (fechas[pos + 1] == ok.entrada).all() and (
        fechas[pos + h] == ok.salida
    ).all()
    for b, (ini, fin) in cfg["particiones"].items():
        g = ok[ok.bloque == b]
        assert g.corte.ge(ini).all() and g.salida.lt(fin).all()
        if cfg["historia_dentro_del_bloque"]:
            assert g.mensual_inicio.ge(ini).all()
    # Contrato de entrada común: la proyección de dos vistas agrega solo dos campos.
    mensual = ok.set_index("id")[
        ["bloque", "activo", "corte", "mensual_inicio", "mensual_fin"]
    ]
    doble = ok.set_index("id")[list(mensual.columns) + ["diaria_inicio", "diaria_fin"]]
    pd.testing.assert_frame_equal(mensual, doble[mensual.columns])
    cal = tabla.drop_duplicates("corte").sort_values("corte")
    # Contrastar los límites con el extractor original, usando valores ficticios.
    # Los 34 activos ya demostraron tener exactamente este calendario.
    ficticia = pd.DataFrame(1.0, index=fechas, columns=CAMPOS)
    for fila in cal.itertuples():
        vistas = vistas_separadas(
            ficticia, fechas, fila.corte, **cfg["primera_comparacion"]
        )
        assert vistas is not None
        (_, fm), (_, fd) = vistas
        assert (fm[0], fm[-1], fd[0], fd[-1]) == (
            fila.mensual_inicio,
            fila.mensual_fin,
            fila.diaria_inicio,
            fila.diaria_fin,
        )
        assert fm.max() < fd.min() and fd.max() <= fila.corte
    assert all(cal.salida.iloc[:-1].to_numpy() < cal.entrada.iloc[1:].to_numpy())
    cols = [
        "corte",
        "mensual_inicio",
        "mensual_fin",
        "diaria_inicio",
        "entrada",
        "salida",
    ]
    eda = pd.read_csv(BASE / "eda/cadencia_mensual_desarrollo.csv", parse_dates=cols)
    ref = (
        tabla[tabla.salida < "2026-01-01"]
        .groupby(cols)
        .activo.nunique()
        .rename("activos")
        .reset_index()
    )
    pd.testing.assert_frame_equal(ref, eda)
    return cal


def guardar(tabla, fechas, cal, cfg, destino):
    destino.mkdir(exist_ok=True, parents=True)
    tabla.to_csv(destino / "manifiesto.csv", index=False)
    tabla.groupby(["bloque", "motivo"], sort=False).agg(
        casos=("id", "size"), fechas=("corte", "nunique"), activos=("activo", "nunique")
    ).to_csv(destino / "casos_por_bloque.csv")
    pares = []
    for a, b in combinations(cal[cal.elegible].itertuples(), 2):
        if b.mensual_inicio <= a.mensual_fin:
            ruedas = fechas[(fechas >= b.mensual_inicio) & (fechas <= a.mensual_fin)]
            pares.append(
                (
                    a.corte,
                    b.corte,
                    b.mensual_inicio,
                    a.mensual_fin,
                    len(ruedas.to_period("M").unique()),
                    len(ruedas),
                )
            )
    pd.DataFrame(
        pares,
        columns=["corte_a", "corte_b", "inicio_comun", "fin_comun", "meses", "ruedas"],
    ).to_csv(destino / "historia_compartida.csv", index=False)
    fig, axes = plt.subplots(
        2, 1, figsize=(12, 5.8), height_ratios=[1, 1], layout="constrained"
    )
    colores = dict(
        elegible="#16735b",
        historia_anterior="#9a718e",
        salida_en_otro_bloque="#bf5700",
        sin_salida_en_fuente="#354553",
    )
    for ax, desde, hasta in zip(axes, ["2015", "2026"], ["2027", "2026-12"]):
        for b, (ini, fin) in cfg["particiones"].items():
            if desde <= ini < hasta:
                ax.axvline(pd.Timestamp(ini), color="#777777", lw=0.9)
                ax.text(
                    pd.Timestamp(ini),
                    1.21,
                    {
                        "entrenamiento": "Entrenamiento",
                        "configuracion": "Configuración",
                        "umbral": "Umbral",
                        "prueba_retrospectiva": "Prueba",
                    }[b],
                    fontsize=9,
                )
        for motivo, g in cal.groupby("motivo"):
            g = g[g.corte.between(desde, hasta)]
            ax.scatter(
                g.corte,
                [1] * len(g),
                color=colores[motivo],
                label=motivo.replace("_", " "),
                s=24,
            )
        ax.set(
            xlim=(pd.Timestamp(desde), pd.Timestamp(hasta)), ylim=(0.78, 1.4), yticks=[]
        )
    axes[0].set_title("Una marca por corte mensual · 34 activos por fecha", loc="left")
    axes[1].set_title("Detalle de 2026", loc="left")
    axes[0].legend(loc="lower center", ncol=4, frameon=False)
    fig.savefig(destino / "calendario.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ohlc", type=Path)
    parser.add_argument("--destino", type=Path, default=BASE / "verificacion")
    args = parser.parse_args()
    cfg = cargar_config()
    tabla, fechas = construir(args.ohlc, cfg)
    cal = verificar(tabla, fechas, cfg)
    guardar(tabla, fechas, cal, cfg, args.destino)
    print(tabla.groupby(["bloque", "motivo"], sort=False).size().to_string())
