"""Cobertura, solapamientos y patrones OHLC antes de entrenar."""
from itertools import product

import pandas as pd

from ventanas import extraer_ventana, vistas_separadas


def patrones(velas):
    """Detecta eventos con su vela final como índice (solo contexto visible)."""
    o, h, l, c = (velas[nombre] for nombre in ("open", "high", "low", "close"))
    cuerpo = (c - o).abs()
    inferior = velas[["open", "close"]].min(axis=1) - l
    superior = h - velas[["open", "close"]].max(axis=1)
    rango = h - l
    baja_previa = c.shift(3).gt(c.shift(2)) & c.shift(2).gt(c.shift(1))
    return pd.DataFrame({
        "doji": rango.gt(0) & cuerpo.le(.10 * rango),
        "martillo": baja_previa & cuerpo.gt(0) & inferior.ge(2 * cuerpo) & superior.le(.10 * rango),
        "envolvente_alcista": (
            baja_previa & c.shift(1).lt(o.shift(1)) & c.gt(o)
            & o.lt(l.shift(1)) & h.gt(h.shift(1)) & c.gt(o.shift(1))
        ),
    })


def resumen_llaves(llaves):
    return {
        "casos": len(llaves),
        "fechas": len({corte for _, corte in llaves}),
        "activos": len({activo for activo, _ in llaves}),
    }


def resumen_ventana(ventanas, llaves):
    por_activo = {}
    for activo, corte in sorted(llaves):
        por_activo.setdefault(activo, []).append(corte)
    pares_contados = 0
    cruces = []
    solapes = set()
    for activo, cortes in por_activo.items():
        for a, b in zip(cortes, cortes[1:]):
            pares_contados += 1
            compartidas = len(ventanas[activo, a][1].intersection(ventanas[activo, b][1]))
            if compartidas:
                cruces.append(compartidas)
                solapes.add((a, b))
    return {
        **resumen_llaves(llaves),
        "pares_consecutivos_mismo_activo": pares_contados,
        "pares_mismo_activo_con_ruedas_compartidas": len(cruces),
        "pares_distintos_de_fechas_con_ruedas_compartidas": len(solapes),
        "max_ruedas_compartidas": max(cruces, default=0),
    }


def resumir_patrones(vistas, interseccion, primera, destino):
    resultados = []
    largos_minimos = {"doji": 1, "martillo": 4, "envolvente_alcista": 4}
    for (unidad, n), ventanas in vistas.items():
        eventos = {llave: patrones(velas) for llave, (velas, _) in ventanas.items()}
        for alcance, llaves in [("propio", ventanas.keys()), ("comun", interseccion)]:
            for patron, largo_minimo in largos_minimos.items():
                casos = {llave for llave in llaves if eventos[llave][patron].any()}
                al_final = sum(bool(eventos[llave][patron].iloc[-1]) for llave in casos)
                resultados.append({
                    "unidad": unidad, "longitud": n, "alcance": alcance, "patron": patron,
                    "oportunidades": len(llaves),
                    "casos_con_contexto_suficiente": len(llaves) if n >= largo_minimo else 0,
                    **resumen_llaves(casos), "casos_al_final": al_final,
                })
    pd.DataFrame(resultados).to_csv(destino / "patrones_desarrollo.csv", index=False)

    mensual = vistas["meses", primera["meses"]]
    diaria = vistas["ruedas", primera["ruedas"]]
    universo = {llave for llave in mensual.keys() & diaria.keys()
                if mensual[llave][1][-1] < diaria[llave][1][0]}
    ocurrencias = []
    for activo, corte in sorted(universo):
        llave = activo, corte
        velas_m, _ = mensual[llave]
        velas_d, _ = diaria[llave]
        if not patrones(velas_m).doji.iloc[-1]:
            continue
        senales = patrones(velas_d).loc[lambda filas: filas.envolvente_alcista]
        if not senales.empty:
            ocurrencias.append({
                "activo": activo, "corte": corte, "mes_doji": velas_m.index[-1],
                "envolvente_fin": senales.index[0],
            })
    casos = {(fila["activo"], fila["corte"]) for fila in ocurrencias}
    pd.DataFrame([{"oportunidades": len(universo), **resumen_llaves(casos)}]).to_csv(
        destino / "combinacion_patrones_desarrollo.csv", index=False,
    )
    pd.DataFrame(ocurrencias, columns=["activo", "corte", "mes_doji", "envolvente_fin"]).to_csv(
        destino / "ejemplos_combinacion_patrones.csv", index=False,
    )


def analizar_representacion(series, calendario, operaciones, config, destino):
    meses = config["ventanas_mensuales_candidatas"]
    ruedas = config["ventanas_diarias_candidatas"]
    candidatos = [("meses", n) for n in meses] + [("ruedas", n) for n in ruedas]
    vistas = {candidato: {} for candidato in candidatos}
    llaves_piloto = list(operaciones[["activo", "corte"]].itertuples(index=False, name=None))
    for activo, corte in llaves_piloto:
        for unidad, n in candidatos:
            velas, fechas = extraer_ventana(series[activo], calendario, corte, n, unidad)
            if velas is not None:
                vistas[unidad, n][activo, corte] = velas, fechas

    comun = set.intersection(*(set(ventanas) for ventanas in vistas.values()))
    coberturas = []
    for (unidad, n), ventanas in vistas.items():
        for alcance, llaves in [("propio", ventanas.keys()), ("comun", comun)]:
            coberturas.append({
                "unidad": unidad, "longitud": n, "alcance": alcance,
                **resumen_ventana(ventanas, llaves),
            })
    resumen = pd.DataFrame(coberturas)
    resumen.to_csv(destino / "cobertura_ventanas_desarrollo.csv", index=False)
    cruces = []
    elegibles_sin_cruce = {}
    for m, d in product(meses, ruedas):
        mensual, diaria = vistas["meses", m], vistas["ruedas", d]
        llaves = mensual.keys() & diaria.keys()
        elegibles_sin_cruce[m, d] = {
            llave for llave in llaves if mensual[llave][1][-1] < diaria[llave][1][0]
        }
        for alcance, muestra in [("propio", llaves), ("comun", comun)]:
            separados = resumen_llaves(elegibles_sin_cruce[m, d] & muestra)
            compartidas = {
                llave: len(mensual[llave][1].intersection(diaria[llave][1]))
                for llave in muestra
            }
            solapes = {llave for llave, n in compartidas.items() if n > 0}
            cruces.append({
                "meses": m, "ruedas": d, "alcance": alcance, **resumen_llaves(muestra),
                **{f"{k}_sin_cruce": valor for k, valor in separados.items()},
                "casos_con_ruedas_en_ambas_vistas": len(solapes),
                "fechas_con_ruedas_en_ambas_vistas": len({corte for _, corte in solapes}),
                "max_ruedas_en_ambas_vistas": max(compartidas.values(), default=0),
            })
    pd.DataFrame(cruces).to_csv(destino / "combinaciones_ventanas_desarrollo.csv", index=False)
    primera = config["primera_comparacion"]
    llaves_primera = elegibles_sin_cruce[primera["meses"], primera["ruedas"]]
    manifiesto = [
        {"activo": activo, "corte": corte, "interseccion_todas": (activo, corte) in comun,
         "primera_comparacion_sin_cruce": (activo, corte) in llaves_primera,
         **{f"{n}_{unidad}": (activo, corte) in vistas[unidad, n] for unidad, n in candidatos}}
        for activo, corte in sorted(llaves_piloto)
    ]
    pd.DataFrame(manifiesto).to_csv(destino / "elegibilidad_ventanas_desarrollo.csv", index=False)
    resumir_patrones(vistas, comun, primera, destino)
    auditar_cadencia(series, calendario, config, destino)
    return resumen


def auditar_cadencia(series, calendario, config, destino):
    """Cuenta oportunidades factibles con un corte por mes y tenencias sin superposición."""
    primera = config["primera_comparacion"]
    tenencia = config["ruedas_de_tenencia_piloto"]
    anterior = -tenencia
    meses_usados = set()
    cortes = []
    for i, corte in enumerate(calendario[:-tenencia]):
        mes = corte.to_period("M")
        if mes in meses_usados or i - anterior < tenencia:
            continue
        horizonte = calendario[i:i + tenencia + 1]
        elegibles = [
            vistas for serie in series.values()
            if horizonte.isin(serie.index).all()
            if (vistas := vistas_separadas(serie, calendario, corte, **primera)) is not None
        ]
        if not elegibles:
            continue
        (_, mensual), (_, diaria) = elegibles[0]
        cortes.append({
            "corte": corte, "mensual_inicio": mensual[0], "mensual_fin": mensual[-1],
            "diaria_inicio": diaria[0], "entrada": horizonte[1], "salida": horizonte[-1],
            "activos": len(elegibles),
        })
        anterior = i
        meses_usados.add(mes)
    pd.DataFrame(cortes).to_csv(destino / "cadencia_mensual_desarrollo.csv", index=False)
