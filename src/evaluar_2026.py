"""Verifica el cierre de 3B y evalúa las cuatro estrategias congeladas en 2026."""

import argparse
import csv
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from cargar_imagenes import cargar_dos_vistas, filas_del_bloque
from cartera import CAPITAL_INICIAL, simular
from cnn_modelos import MODELOS, predecir
from datos_3b import CONTROL_3A, guardar_json, huella, leer_json, seleccionar_manifiesto, verificar_huella
from entrenar_3b import PLAN, comprobar_plan, guardar_csv, metricas
from generar_imagenes import verificar_cargadores
from seleccionar_3b import CONGELADO, PUBLICO, comprobar_checkpoint, recargar_congelado, reproducir
from ventanas import BASE, cargar_config
from verificar_protocolo import construir, verificar
import matplotlib.pyplot as plt


CONFIG = BASE / "config/evaluacion_2026.json"
FECHAS = ["mensual_inicio", "mensual_fin", "diaria_inicio", "diaria_fin", "corte", "entrada", "salida"]
NOMBRES = {
    "mensual": "CNN mensual",
    "mensual_diaria": "CNN mensual + diaria",
    "comprar_siempre": "Comprar siempre",
    "efectivo": "Efectivo",
}


def verificar_insumos(ohlc, corrida, congelado, protocolo, plan):
    bloque = corrida["bloque"]
    regla = congelado["regla"]
    umbrales = {n: congelado["modelos"][n]["umbral"] for n in MODELOS}
    umbrales.update(comprar_siempre=0.0, efectivo=1.01)
    if (
        corrida["umbrales"] != umbrales
        or corrida["epocas"] != {n: congelado["modelos"][n]["epoca"] for n in MODELOS}
        or corrida["vistas"] != protocolo["primera_comparacion"]
        or corrida["ruedas_de_tenencia"] != protocolo["ruedas_de_tenencia_piloto"]
        or corrida["capital_inicial"] != regla["capital_inicial"] or regla["capital_inicial"] != CAPITAL_INICIAL
        or corrida["regla_compra"] != regla["compra"] or regla["compra"] != "p >= umbral"
        or corrida["costo_total_compra"] != regla["costo_total_compra"]
        or regla["costo_total_compra"] != protocolo["costo_total_piloto"]
        or corrida["efectivo_por_periodo"] != 0 or regla["efectivo_por_periodo"] != 0
        or protocolo["efectivo_por_periodo"] != 0
    ):
        raise ValueError("La configuración de 2026 difiere de las reglas congeladas")

    for archivo, esperado in {**congelado["sha256_versionados"],
                               **corrida["sha256_controles_adicionales"]}.items():
        verificar_huella(BASE / archivo, esperado)
    verificar_huella(ohlc, congelado["ohlc_sha256"])
    indice = BASE / congelado["indice_local"]
    verificar_huella(indice, congelado["indice_sha256"])
    for modelo in congelado["modelos"].values():
        verificar_huella(BASE / congelado["pesos_y_probabilidades_locales"] / modelo["pesos"]["archivo"],
                         modelo["pesos"]["sha256"])

    tabla, calendario = construir(ohlc, protocolo)
    verificar(tabla, calendario, protocolo)
    manifiesto = pd.read_csv(BASE / congelado["manifiesto"], parse_dates=FECHAS)
    pd.testing.assert_frame_equal(manifiesto, tabla)
    elegibles = manifiesto.loc[manifiesto.elegible]
    forma = tuple(plan["resolucion_rgb"])
    control = verificar_cargadores(elegibles, indice, forma)
    if control != leer_json(CONTROL_3A)["bloques"]:
        raise ValueError("Los IDs, el orden o los SHA-256 de los PNG difieren de 3A")
    filas = elegibles.loc[elegibles.bloque.eq(bloque)].reset_index(drop=True)
    filas[FECHAS] = filas[FECHAS].apply(lambda fecha: fecha.dt.strftime("%Y-%m-%d"))
    por_corte = filas.groupby("corte", sort=False).size()
    if (not filas.id.is_unique or por_corte.index.tolist() != corrida["cortes"]
            or not por_corte.eq(corrida["elegibles_por_corte"]).all()
            or corrida["ejemplo_id"] not in set(filas.id)):
        raise ValueError("La retrospectiva difiere de las claves reservadas")
    return filas, indice, control


def verificar_recarga(ohlc, indice, congelado, plan, protocolo):
    destino = BASE / congelado["pesos_y_probabilidades_locales"]
    ruta = destino / "checkpoints.json"
    verificar_huella(ruta, congelado["checkpoints_sha256"])
    checkpoint = leer_json(ruta)
    for nombre in MODELOS:
        esperado = congelado["modelos"][nombre]
        registrado = checkpoint["modelos"][nombre]
        if (registrado["epoca_elegida"] != esperado["epoca"]
                or registrado["pesos"] != esperado["pesos"]):
            raise ValueError(f"El checkpoint y la congelación difieren para {nombre}")
    comprobar_plan(plan, protocolo)
    comprobar_checkpoint(destino, checkpoint, plan, protocolo, indice)
    args = argparse.Namespace(destino=destino, ohlc=ohlc, indice=indice, publico=PUBLICO)
    reproducir(args, plan, protocolo, checkpoint, seleccionar_manifiesto(), congelado)


def valorar(ohlc, filas, costo):
    # Las fechas y la cobertura se verificaron con claves en el control previo.
    entradas = set(zip(filas.activo, filas.entrada))
    salidas = set(zip(filas.activo, filas.salida))
    aperturas, cierres = {}, {}
    with ohlc.open(encoding="utf-8", newline="") as archivo:
        for rueda in csv.DictReader(archivo):
            clave = (rueda["activo"], rueda["fecha"])
            if clave in entradas:
                aperturas[clave] = Decimal(rueda["open"])
            if clave in salidas:
                cierres[clave] = Decimal(rueda["close"])
    costo_decimal = Decimal(str(costo))
    valores = []
    for fila in filas.itertuples(index=False):
        apertura = aperturas.get((fila.activo, fila.entrada))
        cierre = cierres.get((fila.activo, fila.salida))
        if any(p is None or not p.is_finite() or p <= 0 for p in (apertura, cierre)):
            raise ValueError(f"Falta un precio ajustado válido para {fila.id}")
        bruto = cierre / apertura - 1
        neto = bruto - costo_decimal
        valores.append((float(apertura), float(cierre), float(bruto), float(neto),
                        int(cierre > apertura * (1 + costo_decimal))))
    columnas = ["apertura_ajustada_t1", "cierre_ajustado_t20", "retorno_bruto", "retorno_neto", "etiqueta"]
    return filas.join(pd.DataFrame(valores, columns=columnas)).assign(costo_compra=costo)


def evaluar_carteras(filas, probabilidades, corrida):
    inicial = corrida["capital_inicial"]
    detalle, resumen, decisiones = {}, {}, filas[["id", "activo", "corte", "entrada", "salida",
                                                   "retorno_neto", "etiqueta"]].copy()
    for nombre, umbral in corrida["umbrales"].items():
        p = probabilidades.get(nombre, pd.Series(0.5, index=filas.id))
        resumen[nombre], trayectoria = simular(filas, p, umbral, inicial)
        detalle[nombre] = trayectoria.set_index("corte")
        compra = p.to_numpy() >= umbral
        decisiones[f"compra_{nombre}"] = compra
        asignado = filas.corte.map(detalle[nombre].capital_por_activo)
        aporte = (filas.retorno_neto * asignado).where(compra, 0.0)
        decisiones[f"aporte_capital_{nombre}"] = aporte
        np.testing.assert_allclose(aporte.groupby(filas.corte).sum(),
                                   trayectoria.capital_final - trayectoria.capital_inicial,
                                   rtol=0, atol=1e-12)
        if nombre in probabilidades:
            decisiones[f"p_{nombre}"] = p.to_numpy()

    mensual = decisiones.compra_mensual
    doble = decisiones.compra_mensual_diaria
    decisiones["decision_cambia"] = mensual.ne(doble)
    diferencia = doble.astype(int) - mensual.astype(int)
    n = filas.groupby("corte").id.transform("size")
    aporte = filas.retorno_neto * diferencia / n
    decisiones["aporte_diferencia_corte_pp"] = 100 * aporte
    # Identidad telescópica: capital doble anterior por el cambio del corte,
    # capitalizado después con los factores mensuales de los cortes restantes.
    posterior = (1 + detalle["mensual"].retorno_neto_corte).iloc[::-1].cumprod().shift(fill_value=1)
    anterior = detalle["mensual_diaria"].capital_inicial / inicial
    decisiones["aporte_diferencia_acumulada_pp"] = 100 * aporte * filas.corte.map(anterior * posterior)
    contrastes = (("mensual_diaria", "mensual"), ("mensual", "comprar_siempre"),
                  ("mensual_diaria", "comprar_siempre"))
    deltas = {f"{a}_menos_{b}_pp": 100 * (resumen[a]["retorno_neto_acumulado"]
                                        - resumen[b]["retorno_neto_acumulado"]) for a, b in contrastes}
    np.testing.assert_allclose(decisiones.aporte_diferencia_acumulada_pp.sum(),
                               deltas["mensual_diaria_menos_mensual_pp"], rtol=0, atol=1e-12)
    por_corte = decisiones.assign(
        ambas_compran=mensual & doble, ambas_pasan=~(mensual | doble),
        solo_mensual=mensual & ~doble, solo_doble=~mensual & doble,
    ).groupby("corte", sort=False)
    conteos = por_corte[["ambas_compran", "ambas_pasan", "solo_mensual", "solo_doble", "decision_cambia",
                         "aporte_diferencia_acumulada_pp"]].sum()
    conteos["coinciden"] = conteos.ambas_compran + conteos.ambas_pasan
    for a, b in contrastes:
        conteos[f"{a}_menos_{b}_pp"] = 100 * (detalle[a].retorno_neto_corte - detalle[b].retorno_neto_corte)
    tabla = pd.concat([trayecto.reset_index().assign(estrategia=nombre)
                       for nombre, trayecto in detalle.items()], ignore_index=True)
    resumen = pd.DataFrame.from_dict(resumen, orient="index").rename_axis("estrategia").reset_index()
    return resumen, tabla, decisiones, conteos.reset_index(), deltas


def graficar(tabla, destino):
    fig, ax = plt.subplots(figsize=(9, 4.5), layout="constrained")
    colores = ["#146458", "#a13d17", "#253f72", "#5b6472"]
    estilos = ["--o", ":D", "-s", "-."]
    for (nombre, grupo), color, estilo in zip(tabla.groupby("estrategia", sort=False), colores, estilos):
        fechas = [grupo.corte.iloc[0], *grupo.salida]
        capital = [grupo.capital_inicial.iloc[0], *grupo.capital_final]
        # Transparencia y marcadores de distintos tamaños conservan visibles las curvas coincidentes.
        i = list(NOMBRES).index(nombre)
        ax.plot(pd.to_datetime(fechas), capital, estilo, color=color, label=NOMBRES[nombre],
                markersize=[7, 4, 9, 0][i], markerfacecolor="none",
                linewidth=[2, 2.8, 2.6, 1.5][i], zorder=[4, 5, 3, 2][i])
    ax.set_title("Capital acumulado en la retrospectiva de 2026", loc="left", fontweight="bold")
    ax.set(ylabel="Capital acumulado · inicial 100", xlabel="Inicio y cierres de tenencia")
    ax.set_xticks(pd.to_datetime(fechas), [f"{f[8:10]}/{f[5:7]}" for f in fechas])
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, ncol=2)
    fig.savefig(destino / "capital_acumulado.png", dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ohlc", type=Path)
    parser.add_argument("--destino", type=Path, default=BASE / "verificacion/etapa_4")
    parser.add_argument("--solo-verificar", action="store_true")
    args = parser.parse_args()
    if not args.solo_verificar and args.destino.exists():
        parser.error("El destino ya existe. Use un directorio nuevo para reproducir la corrida.")
    corrida, plan, protocolo = leer_json(CONFIG), leer_json(PLAN), cargar_config()
    verificar_huella(CONGELADO, corrida["congelado_3b_sha256"])
    congelado = leer_json(CONGELADO)
    ohlc = args.ohlc or BASE / corrida["ohlc_local"]
    filas, indice, control = verificar_insumos(ohlc, corrida, congelado, protocolo, plan)
    verificar_recarga(ohlc, indice, congelado, plan, protocolo)
    print(f"Controles completos: {len(filas)} IDs, {filas.corte.nunique()} cortes y PNG de 3A.", flush=True)
    if args.solo_verificar:
        return

    bloque, forma = corrida["bloque"], tuple(plan["resolucion_rgb"])
    pares = list(cargar_dos_vistas(indice, bloque, forma))
    if [identificador for identificador, _ in pares] != filas.id.tolist():
        raise ValueError("Cambió el orden de los tensores antes de predecir")
    imagenes = tuple(np.stack([par[i].pixeles for _, par in pares]) for i in range(2))
    probabilidades = {
        nombre: pd.Series(predecir(recargar_congelado(nombre, congelado), imagenes, plan["lote"]),
                          index=filas.id)
        for nombre in MODELOS
    }
    filas = valorar(ohlc, filas, corrida["costo_total_compra"])
    resumen, tabla, decisiones, conteos, deltas = evaluar_carteras(filas, probabilidades, corrida)
    met = {n: metricas(filas, p.to_numpy(), plan["epsilon_log_loss"])
           for n, p in probabilidades.items()}
    ejemplo = corrida["ejemplo_id"]
    caso = filas.set_index("id").loc[ejemplo].to_dict()
    caso["id"] = ejemplo
    caso["decisiones"] = decisiones.set_index("id").loc[ejemplo].to_dict()
    registro = next(f for f in filas_del_bloque(indice, bloque) if f.id == ejemplo)
    caso["sha256_png"] = {vista: getattr(registro, f"{vista}_sha256") for vista in ("mensual", "diaria")}

    args.destino.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".etapa_4_", dir=args.destino.parent) as carpeta:
        temporal = Path(carpeta)
        for nombre, datos in {"carteras_resumen": resumen, "carteras_por_corte": tabla,
                              "decisiones_por_id": decisiones, "decisiones_por_corte": conteos}.items():
            guardar_csv(datos, temporal / f"{nombre}.csv")
        guardar_json(temporal / "metricas.json", {
            "prediccion": met, "diferencias_economicas": deltas,
            "etiquetas_positivas": int(filas.etiqueta.sum()), "casos": len(filas),
            "coinciden": int(conteos.coinciden.sum()), "cambian": int(conteos.decision_cambia.sum()),
        })
        guardar_json(temporal / "control.json", {
            "commit_3b": corrida["commit_3b"], "congelado_3b_sha256": huella(CONGELADO),
            "configuracion_2026_sha256": huella(CONFIG), "evaluador_sha256": huella(Path(__file__)),
            "recarga_3b_verificada": True, "tolerancia_recarga": plan["tolerancia_recarga"],
            "ohlc_sha256": congelado["ohlc_sha256"], "indice_sha256": congelado["indice_sha256"],
            "manifiesto_reconstruido": True, "png_verificados_por_bloque": control,
            "pesos_verificados": {n: r["pesos"]["sha256"] for n, r in congelado["modelos"].items()},
        })
        guardar_json(temporal / "caso_ko.json", caso)
        for vista in ("mensual", "diaria"):
            png = indice.parent / getattr(registro, f"{vista}_png")
            verificar_huella(png, caso["sha256_png"][vista])
            (temporal / f"{ejemplo}_{vista}.png").write_bytes(png.read_bytes())
        graficar(tabla, temporal)
        temporal.rename(args.destino)
    print(resumen.to_string(index=False))
    print(f"Decisiones que cambian: {conteos.decision_cambia.sum()} de {len(filas)}")


if __name__ == "__main__":
    main()
