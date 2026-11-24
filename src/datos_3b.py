"""Insumos de 3B. El acceso a imágenes y precios operables se limita a 2015–2025."""

import csv
from decimal import Decimal
import hashlib
from itertools import zip_longest
import json

import numpy as np
import pandas as pd

from cargar_imagenes import cargar_dos_vistas, cargar_mensual
from ventanas import BASE


BLOQUES = {"entrenamiento": (2210, 65), "configuracion": (578, 17), "umbral": (986, 29)}
MANIFIESTO = BASE / "verificacion/manifiesto.csv"
CONTROL_3A = BASE / "verificacion/imagenes/controles.json"


def huella(ruta):
    digest = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for trozo in iter(lambda: archivo.read(1024 * 1024), b""):
            digest.update(trozo)
    return digest.hexdigest()


def leer_json(ruta):
    return json.loads(ruta.read_text(encoding="utf-8"))


def guardar_json(ruta, datos):
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")


def verificar_huella(ruta, esperado):
    comprobada = huella(ruta)
    if comprobada != esperado:
        raise ValueError(f"SHA-256 distinto para {ruta}")
    return comprobada


def seleccionar_manifiesto():
    escalas = leer_json(BASE / "config/escalas_imagenes.json")
    verificar_huella(MANIFIESTO, escalas["manifiesto_sha256"])
    verificar_huella(BASE / "config/render.json", escalas["render_sha256"])
    verificar_huella(BASE / "verificacion/imagenes/ids_ajuste.txt", escalas["ids_sha256"])
    filas = pd.read_csv(MANIFIESTO, dtype=str, keep_default_na=False)
    filas = filas[filas.bloque.isin(BLOQUES)]
    if not filas.id.is_unique or not filas.elegible.eq(filas.motivo.eq("elegible").map(
        {True: "True", False: "False"}
    )).all():
        raise ValueError("IDs o elegibilidad del manifiesto inválidos")
    return filas


def filas_elegibles(manifiesto, bloque):
    n, cortes = BLOQUES[bloque]
    filas = manifiesto[manifiesto.bloque.eq(bloque) & manifiesto.elegible.eq("True")]
    if (len(filas) != n or filas.corte.nunique() != cortes
            or not filas.groupby("corte").size().eq(34).all()
            or not filas.corte.is_monotonic_increasing
            or not filas.id.eq(filas.activo + "_" + filas.corte).all()):
        raise ValueError(f"El manifiesto cambió en {bloque}")
    return filas.reset_index(drop=True)


def cargar_bloque(indice, manifiesto, bloque, forma, materializar=True):
    filas = filas_elegibles(manifiesto, bloque)
    registros = zip_longest(filas.id, cargar_mensual(indice, bloque, forma),
                            cargar_dos_vistas(indice, bloque, forma))
    huellas = {vista: hashlib.sha256() for vista in ("mensual", "diaria")}
    forma_lote = (len(filas), *forma)
    imagenes = tuple(np.empty(forma_lote, dtype=np.uint8) for _ in huellas) if materializar else ()
    for i, (identificador, simple, doble) in enumerate(registros):
        if simple is None or doble is None or identificador != simple[0] or identificador != doble[0]:
            raise ValueError(f"Orden o cobertura incorrectos en {bloque}: {identificador}")
        mensual, diaria = doble[1]
        if simple[1].ruta != mensual.ruta or simple[1].sha256 != mensual.sha256:
            raise ValueError(f"Los cargadores apuntan a distintos PNG mensuales: {identificador}")
        for j, (vista, entrada) in enumerate(zip(huellas, (mensual, diaria))):
            if entrada.pixeles.shape != forma or entrada.pixeles.dtype != np.uint8:
                raise ValueError(f"Tensor RGB incorrecto para {identificador} ({vista})")
            huellas[vista].update(f"{identificador},{entrada.sha256}\n".encode("ascii"))
            if materializar:
                imagenes[j][i] = entrada.pixeles
    hashes = {vista: digest.hexdigest() for vista, digest in huellas.items()}
    esperado = leer_json(CONTROL_3A)["bloques"][bloque]["sha256_id_y_png_en_orden"]
    if hashes != esperado:
        raise ValueError(f"Los PNG ordenados no coinciden con 3A: {bloque}")
    control = {"casos": len(filas), "cortes": filas.corte.nunique(),
               "mensuales_identicos_entre_cargadores": len(filas),
               "sha256_id_y_png_en_orden": hashes, "forma_tensor_por_vista": list(forma_lote),
               "dtype": "uint8"}
    return imagenes, control


def resultados_ohlc(ruta, filas, cfg):
    """Calcula etiquetas sólo para las filas elegibles de los bloques solicitados."""
    bloques = set(filas.bloque)
    if not bloques or bloques - BLOQUES.keys() or not filas.elegible.eq("True").all():
        raise ValueError("3B solo acepta filas elegibles de entrenamiento, configuración o umbral")
    verificar_huella(ruta, cfg["fuente"]["sha256"])
    claves_precios = set(zip(filas.activo, filas.entrada)) | set(zip(filas.activo, filas.salida))
    limites = [cfg["particiones"][bloque] for bloque in bloques]
    claves = set()
    precios = {}
    with ruta.open(encoding="utf-8", newline="") as archivo:
        for rueda in csv.DictReader(archivo):
            fecha = rueda["fecha"]
            if not any(inicio <= fecha < fin for inicio, fin in limites):
                continue
            clave = (rueda["activo"], fecha)
            if clave in claves:
                raise ValueError(f"Sesión duplicada: {clave}")
            claves.add(clave)
            if clave in claves_precios:
                precios[clave] = (Decimal(rueda["open"]), Decimal(rueda["close"]))
    if set(precios) != claves_precios:
        raise ValueError("Falta un precio esperado de entrada o salida")
    fechas = sorted({fecha for _, fecha in claves})
    calendario = {fecha: i for i, fecha in enumerate(fechas)}
    meses = pd.DatetimeIndex(fechas).to_period("M")
    horizonte = cfg["ruedas_de_tenencia_piloto"]
    aperturas, cierres, retornos, etiquetas = [], [], [], []
    costo = Decimal(str(cfg["costo_total_piloto"]))
    for _, corte in filas.groupby("corte", sort=False):
        referencia = corte.iloc[0]
        pos = calendario[referencia.corte]
        inicio, fin = cfg["particiones"][referencia.bloque]
        mensual = meses.searchsorted(meses[pos] - cfg["primera_comparacion"]["meses"])
        mensual_fin = meses.searchsorted(meses[pos]) - 1
        diario = pos - cfg["primera_comparacion"]["ruedas"] + 1
        ventanas = {
            "mensual_inicio": fechas[mensual], "mensual_fin": fechas[mensual_fin],
            "diaria_inicio": fechas[diario], "diaria_fin": fechas[pos],
            "entrada": fechas[pos + 1], "salida": fechas[pos + horizonte],
        }
        if (not inicio <= fechas[mensual] <= fechas[mensual_fin] < fechas[diario]
                <= referencia.corte < ventanas["entrada"] <= ventanas["salida"] < fin
                or any(not corte[k].eq(valor).all() for k, valor in ventanas.items())):
            raise ValueError(f"Fechas o frontera incorrectas para {referencia.corte}")
        ruedas = fechas[mensual:mensual_fin + 1] + fechas[diario:pos + horizonte + 1]
        for fila in corte.itertuples(index=False):
            if any((fila.activo, fecha) not in claves for fecha in ruedas):
                raise ValueError(f"Cobertura incompleta para {fila.id}")
            apertura = precios[(fila.activo, fila.entrada)][0]
            cierre = precios[(fila.activo, fila.salida)][1]
            if not all(p.is_finite() and p > 0 for p in (apertura, cierre)):
                raise ValueError(f"Precio ajustado no válido para {fila.id}")
            aperturas.append(float(apertura))
            cierres.append(float(cierre))
            retornos.append(float(cierre / apertura - 1 - costo))
            etiquetas.append(int(cierre > apertura * (1 + costo)))
    bruto = np.asarray(cierres) / np.asarray(aperturas) - 1
    np.testing.assert_allclose(retornos, bruto - float(costo), rtol=0, atol=1e-12)
    np.testing.assert_array_equal(etiquetas, np.asarray(retornos) > 0)
    return filas[["id", "bloque", "activo", "corte", "entrada", "salida"]].assign(
        apertura_ajustada_t1=aperturas, cierre_ajustado_t20=cierres,
        retorno_bruto=bruto, costo_compra=float(costo), retorno_neto=retornos, etiqueta=etiquetas,
    )
