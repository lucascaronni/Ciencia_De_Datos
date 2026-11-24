# Iteración 2 · Comprar o pasar con velas mensuales y diarias

El experimento continúa la propuesta de Gabriel de sumar una vista corta a un gráfico de contexto. El informe vinculará la pregunta con esa explicación y citará los trabajos usados como antecedentes de visión sobre velas.

| Para encontrar | Abrir |
|---|---|
| Reparto en chats y traspasos | [Plan de trabajo](informe/plan_de_trabajo.md) |
| Pregunta, decisión y evaluación | [Diseño del experimento](informe/diseno.md) |
| Fechas y supuestos del piloto | [Configuración](config/experimento.json) |
| EDA de industrias y volatilidad | [Gráfico](eda/sectores_y_volatilidad.png) y [datos por activo](eda/activos_desarrollo.csv) |
| Comparación visual de escalas | [KO](eda/escalas_KO.png), [UNP](eda/escalas_UNP.png) y [COP](eda/escalas_COP.png) |
| Cruce entre sectores y volatilidad | [Tabla de cobertura](eda/sectores_y_volatilidad.csv) |
| Cantidad de casos y solapamiento mensual | [Recuento](eda/cobertura_mensual_desarrollo.csv) |
| Compra hipotética al día siguiente | [Operaciones candidatas de desarrollo](eda/operaciones_desarrollo.csv) |
| Variación entre cortes | [Frecuencia positiva por fecha](eda/resultados_por_fecha_desarrollo.csv) |
| Ejecutar el EDA | [Script](src/eda_desarrollo.py) |

## Reproducir el primer EDA

Desde la raíz de Trabajo_Final_Ciencias, con Python y NumPy, pandas y Matplotlib instalados:

```bash
MPLBACKEND=Agg python3 iteracion_2/src/eda_desarrollo.py \
  'entregables/02 — Base semanal/OHLC_diario_yf20261114T2019Z.csv' \
  '02 — Base semanal/BASE_SEMANAL/indice_imagenes.csv' \
  'entregables/02 — Base semanal/Fuente_OHLC_diario_yf20261114T2019Z.md'
```

La fuente es la versión congelada yf20261114T2019Z del proyecto. El EDA filtra precios y cortes a desarrollo antes de calcular volatilidad y retornos. Del índice anterior solo lee activo, fecha de corte y bloque. Los resultados representan un piloto metodológico con fechas de corte reutilizadas. La nota de fuente documenta el carácter retrospectivo del universo y de los precios ajustados.

Para reproducir la comparación de escalas, ejecutar `python3 iteracion_2/src/comparar_escalas.py` con la ruta del mismo CSV OHLC como argumento.
