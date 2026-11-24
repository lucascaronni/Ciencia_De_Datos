# Iteración 2 · Comprar o pasar con velas mensuales y diarias

¿Una CNN mensual + diaria mejora el retorno neto de decidir entre comprar y mantener efectivo frente a una CNN mensual, sobre las mismas oportunidades? El EDA de desarrollo prepara las entradas de esa comparación. El experimento continúa la propuesta de Gabriel de sumar una vista corta a un gráfico de contexto.

## EDA y representación · Desarrollo 2015–2025

| Para encontrar | Abrir |
|---|---|
| Hallazgos, fuentes y decisiones para Lucas y Simon | [Nota de revisión](eda/representacion.md) |
| Qué ve la CNN en cada longitud | [Figura de KO con las cinco ventanas](eda/ventanas_KO.png) |
| Casos, fechas, activos y solapamiento entre cortes | [Cortes elegibles para t+20](eda/cortes_desarrollo.csv) · [Cobertura de ventanas](eda/cobertura_ventanas_desarrollo.csv) · [Intersección por activo y corte](eda/elegibilidad_ventanas_desarrollo.csv) |
| Ruedas compartidas por la mensual y la diaria | [Combinaciones de ventanas](eda/combinaciones_ventanas_desarrollo.csv) |
| Precio ajustado, log y min–max sobre las mismas velas | [KO, baja](eda/escalas_KO.png) · [UNP, media](eda/escalas_UNP.png) · [COP, alta](eda/escalas_COP.png) · [Medidas](eda/medidas_escalas_desarrollo.csv) |
| Tres patrones OHLC y una secuencia exploratoria | [Recuentos](eda/patrones_desarrollo.csv) · [Secuencia](eda/combinacion_patrones_desarrollo.csv) · [Casos reales](eda/ejemplos_combinacion_patrones.csv) |
| Cobertura, volatilidad y resultados por grupo | [Activos](eda/activos_desarrollo.csv) · [Sector](eda/resultados_por_sector_desarrollo.csv) · [Tercil](eda/resultados_por_tercil_desarrollo.csv) · [Cruce](eda/resultados_por_sector_y_tercil_desarrollo.csv) · [Figura sectorial](eda/sectores_y_volatilidad.png) |
| Concentración por fecha en el piloto | [Figura](eda/resultados_por_fecha_desarrollo.png) · [Tabla](eda/resultados_por_fecha_desarrollo.csv) · [Operaciones](eda/operaciones_desarrollo.csv) |
| Procedimiento y código | [EDA](src/eda_desarrollo.py) · [Ventanas](src/ventanas.py) · [Cobertura y patrones](src/analizar_representacion.py) · [Figuras de escalas](src/comparar_escalas.py) |
| Alcance y coordinación | [Diseño](informe/diseno.md) · [Plan de trabajo](informe/plan_de_trabajo.md) · [Configuración](config/experimento.json) |

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

El SHA-256 esperado del OHLC congelado `yf20261114T2019Z` es `7906de97be2145f79434dcb1f0a474d2c01ed1da7cc4a7dad1ce63c35683eb31`. Los tres insumos locales se identifican por ruta y el repositorio versiona los resultados derivados. El EDA toma únicamente activo y fecha de corte del índice anterior. El desarrollo de esta iteración abarca 2015–2025 y requiere que t+20 también caiga en ese bloque. Los datos de 2026 quedan reservados para el diseño de evaluación.
