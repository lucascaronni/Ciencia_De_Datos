# Iteración 2 · Comprar o mantener efectivo

¿Agregar nueve velas diarias a una CNN de seis velas mensuales mejora el retorno neto de toda la cartera? Lucas lleva adelante esta iteración. El diseño fija una evaluación retrospectiva de cuatro cortes de 2026 y deja la confirmación para un período futuro.

## Etapa 3 · Generador de imágenes

| Para encontrar | Abrir |
|---|---|
| Ejecutar desde el workspace | [Comando para reproducir](#reproducir-las-imágenes) |
| Implementación | [Generador](src/generar_imagenes.py) · [Render de velas](src/render_velas.py) · [Cargadores](src/cargar_imagenes.py) |
| Escala y procedencia del ajuste | [Parámetros del render](config/render.json) · [Escalas congeladas](config/escalas_imagenes.json) · [2.210 IDs de ajuste](verificacion/imagenes/ids_ajuste.txt) |
| Resultados y límites | [Resumen de verificaciones](informe/generador.md) · [Recuentos y hashes](verificacion/imagenes/controles.json) · [Métricas de recorte y detalle](verificacion/imagenes/metricas.csv) |
| KO al 14 de julio de 2015 | [Figura para clase](verificacion/imagenes/KO_2015-07-14_explicado.png) · [PNG mensual compartido](verificacion/imagenes/KO_2015-07-14_mensual.png) · [PNG diario](verificacion/imagenes/KO_2015-07-14_diaria.png) · [OHLC y log de las 15 velas](verificacion/imagenes/KO_2015-07-14_velas.csv) |

### Reproducir las imágenes

Desde la raíz del repositorio, con el OHLC congelado en la ruta del workspace:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-imagenes.txt
ohlc_iteracion2='../entregables/02 — Base semanal/OHLC_diario_yf20261114T2019Z.csv'
python src/generar_imagenes.py "$ohlc_iteracion2"
```

El comando reconstruye los controles de fechas, recalcula el ajuste de los 2.210 casos de entrenamiento y lo contrasta con los parámetros congelados. Escribe `data/imagenes/indice.csv`, los 7.820 PNG bajo `data/imagenes/cache/` y la evidencia en `data/imagenes/verificacion/`. `--sin-cache` redibuja el lote completo y `--destino` permite elegir otra carpeta local. Para una ruta distinta del OHLC, pasarla como primer argumento. El SHA-256 esperado figura en [Configuración del experimento](config/experimento.json).

Para repetir también la lectura de los dos PNG de KO con Keras, ejecutar en el mismo entorno:

```bash
python -m pip install 'keras==3.10.0' 'jax[cpu]==0.4.30' 'scipy==1.13.1'
KERAS_BACKEND=jax python src/generar_imagenes.py "$ohlc_iteracion2" --verificar-keras
```

## Diseño de la comparación

1. [Protocolo en lenguaje simple y criterios del generador](informe/protocolo.md)
2. [Gráfico del calendario y las fronteras](verificacion/calendario.png)
3. [Tabla de casos y descartes por bloque](verificacion/casos_por_bloque.csv) · [Detalle por activo y corte](verificacion/manifiesto.csv)
4. [Ejemplo numérico de las cuatro estrategias y recorrido real de KO](informe/ejemplo.md)

### Reproducir el diseño

Desde la raíz del repositorio, con Python, pandas, NumPy y Matplotlib:

```bash
python3 src/verificar_protocolo.py '../entregables/02 — Base semanal/OHLC_diario_yf20261114T2019Z.csv'
```

El comando comprueba la huella del insumo local, reproduce el calendario del EDA, valida fechas, bloques y claves compartidas, y regenera las tablas y el gráfico en `verificacion/`. El manifiesto contiene exclusivamente identificadores, fechas y elegibilidad. [Configuración](config/experimento.json) · [Código](src/verificar_protocolo.py)

## EDA y representación · Desarrollo 2015–2025

| Para encontrar | Abrir |
|---|---|
| Hallazgos, fuentes y decisiones para la etapa de diseño | [Nota de revisión](eda/representacion.md) |
| Qué ve la CNN en cada longitud | [Figura de KO con las ventanas](eda/ventanas_KO.png) |
| Casos, fechas, activos y solapamiento entre cortes | [Cortes elegibles para t+20](eda/cortes_desarrollo.csv) · [Cobertura de ventanas](eda/cobertura_ventanas_desarrollo.csv) · [Intersección por activo y corte](eda/elegibilidad_ventanas_desarrollo.csv) |
| Vistas separadas y más cortes de desarrollo | [Combinaciones sin cruce](eda/combinaciones_ventanas_desarrollo.csv) · [Cadencia mensual](eda/cadencia_mensual_desarrollo.csv) |
| Escalas sobre las mismas velas y modelado estocástico | [KO, baja](eda/escalas_KO.png) · [UNP, media](eda/escalas_UNP.png) · [COP, alta](eda/escalas_COP.png) · [Medidas](eda/medidas_escalas_desarrollo.csv) |
| Tres patrones OHLC y una secuencia exploratoria | [Recuentos](eda/patrones_desarrollo.csv) · [Secuencia](eda/combinacion_patrones_desarrollo.csv) · [Casos reales](eda/ejemplos_combinacion_patrones.csv) |
| Cobertura, volatilidad y resultados por grupo | [Activos](eda/activos_desarrollo.csv) · [Sector](eda/resultados_por_sector_desarrollo.csv) · [Tercil](eda/resultados_por_tercil_desarrollo.csv) · [Cruce](eda/resultados_por_sector_y_tercil_desarrollo.csv) · [Figura sectorial](eda/sectores_y_volatilidad.png) |
| Concentración por fecha en el piloto | [Figura](eda/resultados_por_fecha_desarrollo.png) · [Tabla](eda/resultados_por_fecha_desarrollo.csv) · [Operaciones](eda/operaciones_desarrollo.csv) |
| Procedimiento y código | [EDA](src/eda_desarrollo.py) · [Ventanas](src/ventanas.py) · [Cobertura y patrones](src/analizar_representacion.py) · [Figuras de escalas](src/comparar_escalas.py) |
| Alcance y coordinación | [Diseño](informe/protocolo.md) · [Plan de trabajo](informe/plan_de_trabajo.md) · [Configuración](config/experimento.json) |

La primera comparación usa 6 meses cerrados y una vista separada de 9 ruedas. Para el renderizado inicial se eligió [log relativo a la primera apertura de cada vista](eda/representacion.md#modelado-estocástico-y-escalas).

Los retornos corresponden al piloto de desarrollo. Usan costo total supuesto de 0,20 %, entrada en la apertura ajustada de t+1 y salida al cierre ajustado de t+20.

## Reproducir desde el workspace

Ejecutar desde `iteracion_2` con Python, NumPy, pandas y Matplotlib. Se verificó con Python 3.9.6, NumPy 2.0.2, pandas 2.3.3 y Matplotlib 3.9.4.

```bash
ohlc_iteracion2='../entregables/02 — Base semanal/OHLC_diario_yf20261114T2019Z.csv'
indice_cortes='../02 — Base semanal/BASE_SEMANAL/indice_imagenes.csv'
nota_ohlc='../entregables/02 — Base semanal/Fuente_OHLC_diario_yf20261114T2019Z.md'

shasum -a 256 "$ohlc_iteracion2"
MPLBACKEND=Agg python3 src/eda_desarrollo.py "$ohlc_iteracion2" "$indice_cortes" "$nota_ohlc"
MPLBACKEND=Agg python3 src/comparar_escalas.py "$ohlc_iteracion2"
```

El SHA-256 esperado del OHLC congelado `yf20261114T2019Z` es `7906de97be2145f79434dcb1f0a474d2c01ed1da7cc4a7dad1ce63c35683eb31`. Los tres insumos locales se identifican por ruta y el repositorio versiona los resultados derivados. El EDA toma únicamente activo y fecha de corte del índice anterior. El desarrollo de esta iteración abarca 2015–2025 y requiere que t+20 también caiga en ese bloque. El manifiesto de 2026 se construye con fechas y cobertura.
