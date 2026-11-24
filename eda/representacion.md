# EDA y representación · Desarrollo 2015–2025

La comparación posterior medirá si sumar velas diarias a las mensuales mejora el retorno neto de comprar o quedarse en efectivo en las mismas oportunidades. Para este EDA se usó el calendario de cortes de la primera iteración. Se ampliaron las fechas de desarrollo hasta el 31/12/2025 y se recalcularon los retornos desde el OHLC congelado. Los datos de 2026 quedan fuera del análisis. Su eventual uso para evaluación requiere comprobar qué fechas ya se consultaron en la primera iteración.

## Universo y concentración

El CSV tiene **2.766 ruedas** por activo para los **34 activos de 11 sectores**, del 02/01/2015 al 31/12/2025. Hay 39 cortes candidatos de 34 activos cada uno. Quedan 38 cortes y 1.292 operaciones tras excluir el 12/12/2025, cuyo horizonte t+20 rebasa desarrollo. El calendario heredado ofrece dos cortes elegibles en 2025. [Activos](activos_desarrollo.csv) · [Cortes y exclusiones](cortes_desarrollo.csv)

Las cifras usan apertura ajustada de t+1, cierre ajustado de t+20 y **costo total supuesto de 0,20 %**. Bajo ese piloto, 804 de 1.292 operaciones (62,2 %) fueron positivas y el retorno neto medio fue +2,51 %. El 20/03/2020 alcanzó +26,41 % de media con 34 de 34 positivos. Ese corte, el 25/09/2015 y el 21/12/2018 suman 36,1 % de los retornos medios de los cortes con media positiva. Si se retiran los tres como sensibilidad descriptiva, la media baja a +1,46 %. El mínimo fue −6,29 % el 24/12/2015. Los mínimos de proporción positiva (6 de 34) se dieron el 16/09/2022 y el 15/09/2023. [Figura temporal](resultados_por_fecha_desarrollo.png) · [Tabla](resultados_por_fecha_desarrollo.csv) · [Operaciones](operaciones_desarrollo.csv)

La volatilidad histórica va de 17,8 % a 39,1 %. El gráfico por fecha anualiza el desvío de los últimos 20 retornos diarios al corte por activo y promedia los activos. Los terciles bajo, medio y alto tienen 11, 12 y 11 activos y 58,1 %, 67,3 % y 60,8 % de operaciones positivas bajo el mismo piloto. Materiales básicos, comunicaciones e inmobiliario tienen dos activos cada uno. Todo consumo defensivo queda en el tercil bajo. De las 33 celdas sector × tercil, 10 están vacías y 16 tienen un solo activo. Simon debe cotejar la clasificación, los terciles recalculados y la representatividad por grupo y fecha. La selección del universo y el ajuste de precios de Yahoo son retrospectivos. [Mapa de cobertura](sectores_y_volatilidad.png) · [Sector](resultados_por_sector_desarrollo.csv) · [Tercil](resultados_por_tercil_desarrollo.csv) · [Cruce](resultados_por_sector_y_tercil_desarrollo.csv)

## Ventanas y muestra común

La primera comparación usa **6 meses cerrados frente a 6 meses cerrados + 9 ruedas**. Por activo y corte, la última rueda de la mensual debe preceder a la primera de la diaria. La vela mensual toma apertura inicial, máximo, mínimo y cierre final. La diaria termina en el corte. La CNN mensual y la de dos vistas deben usar exactamente las mismas oportunidades y la misma rama mensual.

| Meses cerrados | Casos con 9 ruedas sin cruce | Fechas | Activos | Pares consecutivos de fechas con ruedas mensuales compartidas |
|---|---:|---:|---:|---:|
| 3 | 1.292 | 38 | 34 | 0 de 37 |
| **6** | **1.258** | **37** | **34** | 34 de 36 |
| 9 | 1.224 | 36 | 34 | 33 de 35 |
| 12 | 1.190 | 35 | 34 | 34 de 34 |

Comparar los cuatro largos en las mismas oportunidades requiere las **1.190 claves comunes**. Doce meses agrega más contexto y comparte hasta 192 ruedas entre cortes consecutivos del mismo activo. Seis meses comparte hasta 65. En los cortes heredados, 9 ruedas es la mayor longitud diaria fija sin perder casos por cruce. Con mensual de 6 meses, 10 ruedas comparten una sesión en 68 casos y 20 ruedas cruzan en los 1.258. Las opciones con cruces quedan en el recuento de factibilidad. Una ventana de 20 ruedas con separación requeriría terminar la mensual en el último mes completo anterior al inicio de la diaria. En esa variante, ambos comparadores tendrían que recibir esa misma mensual. [Recuentos](cobertura_ventanas_desarrollo.csv) · [Cruces](combinaciones_ventanas_desarrollo.csv) · [Claves elegibles](elegibilidad_ventanas_desarrollo.csv)

En KO al **12/09/2025**, la mensual de 6 velas usa ruedas del **03/03 al 29/08** y la diaria de 9 usa del **02/09 al 12/09**. En ese corte, ampliar a diez arrastra la última rueda de agosto. [Figura de KO](ventanas_KO.png)

### Más oportunidades dentro de desarrollo

Con el primer corte factible de cada mes, 6 meses + 9 ruedas y al menos 20 ruedas entre cortes, hay **125 fechas y 4.250 casos elegibles** entre julio de 2015 y noviembre de 2025. En cada fecha, la salida del piloto queda como máximo en el corte siguiente y la entrada siguiente es posterior. Este recuento cuantifica cobertura antes de dividir datos o generar imágenes. Los cortes cercanos comparten parte de la historia mensual, y los 34 activos de una fecha comparten el entorno de mercado. Conviene medir variación y desempeño por fecha, con todos sus activos en el mismo bloque. Se conserva 2026 como reserva hasta verificar la independencia y la cobertura de sus cortes. El OHLC congelado empieza en 2015. [Calendario alternativo](cadencia_mensual_desarrollo.csv)

## Modelado estocástico y escalas

El movimiento browniano geométrico ofrece un punto de partida para pensar movimientos proporcionales. En ese modelo, el logaritmo de la razón de precios expresa el retorno logarítmico. La volatilidad condicional puede variar en el tiempo, como formaliza ARCH. Para este proyecto, esto motiva probar una representación relativa y conservar la diferencia visual entre períodos tranquilos y agitados. Los supuestos del movimiento browniano geométrico no quedan validados por dibujar en log. [MIT OpenCourseWare, cálculo estocástico](https://ocw.mit.edu/courses/18-642-topics-in-mathematics-with-applications-in-finance-fall-2024/mit18_642_f24_lec19_1.pdf) · [Engle, 1982](https://doi.org/10.2307/1912773)

| Escala | Qué representa |
|---|---|
| Precio ajustado | Distancias y amplitud en USD ajustados. |
| Log natural | Distancias logarítmicas. Conserva orden y dirección, y puede cambiar la proporción entre cuerpo y mechas. |
| Min–max por vista | Transforma con el mínimo Low y máximo High de esa vista. Preserva proporciones internas y lleva todas las amplitudes a 1. |
| **Relativo lineal** | **Candidato inicial para preservar la forma.** Aplica `100 × (P/P₀ − 1)` a los cuatro campos. `P₀` es la apertura inicial de la propia vista. Mantiene las proporciones entre segmentos de la vela y la amplitud en relación con el nivel inicial. |
| Log relativo | Aplica `100 × ln(P/P₀)` con la misma referencia causal. Iguala las distancias de movimientos multiplicativos iguales y conserva dirección. Se prueba como cambio controlado de escala. |

La apertura inicial se calcula por separado en cada vista. En las muestras de 6 meses, KO cubre **11,95 puntos porcentuales** en la escala relativa lineal y COP **26,39**. Min–max muestra amplitud 1 en ambos. En la vela de agosto de COP, la razón mecha inferior/cuerpo es 0,78 en precio ajustado y en relativo lineal, y 0,81 en log. Las dos columnas relativas de las figuras usan límites comunes a KO, UNP y COP por frecuencia para ilustrar el efecto. [KO](escalas_KO.png) · [UNP](escalas_UNP.png) · [COP](escalas_COP.png) · [Medidas](medidas_escalas_desarrollo.csv)

Para imágenes de la CNN, calibrar límites y resolución por vista **solo con entrenamiento de cada partición**, aplicar los mismos límites en evaluación y medir cuántas velas se recortan o quedan por debajo de un píxel. Mantener ancho de velas, márgenes y resolución comparables. `keras.layers.Rescaling(1/255)` transforma intensidades de píxeles después del dibujo. La separación mensual/diaria evita duplicar una rueda dentro del ejemplo. El control de fuga temporal exige además respetar corte, horizonte y fronteras entre bloques. [Scikit-learn, fuga de datos](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage) · [Keras, Rescaling](https://keras.io/api/layers/preprocessing_layers/image_preprocessing/rescaling/)

## Patrones OHLC

`B = |C − O|` es el cuerpo, `R = H − L` el rango y las mechas son `H − max(O,C)` y `min(O,C) − L`. La caída previa se operacionaliza como tres cierres consecutivos descendentes hasta la vela anterior al disparo. En la envolvente, el tercero es el de la primera vela del patrón. Se exige que todo el contexto esté visible. Los umbrales numéricos son del EDA.

| Patrón | Regla sobre OHLC ajustado | Casos entre 1.292 vistas de 9 ruedas |
|---|---|---:|
| Doji | `R > 0` y `B ≤ 0,10 × R`. | 825, en 38 fechas y 34 activos. [Ponsi, cap. 14](https://onlinelibrary.wiley.com/doi/10.1002/9781119204800.ch14) |
| Martillo | Caída previa, `B > 0`, mecha inferior ≥ `2 × B` y superior ≤ `0,10 × R`. | 48, en 23 fechas y 27 activos. [Ponsi, cap. 13, p. 144](https://onlinelibrary.wiley.com/doi/10.1002/9781119204800.ch13) · [Manual, p. 25](https://drive.google.com/file/d/1zz5J7nYJ4EPZVtIJVCf-_pt9IVoK_K4J/view) |
| Envolvente alcista | Caída previa, primera vela bajista y segunda alcista, `O₂ < L₁`, `H₂ > H₁` y `C₂ > O₁`. Variante estricta de rango completo. | 14, en 10 fechas y 12 activos. [Ponsi, cap. 13, figs. 13.7–13.8](https://onlinelibrary.wiley.com/doi/10.1002/9781119204800.ch13) |

Los conteos son casos con alguna ocurrencia visible. El CSV incluye la presencia en la última vela y el contexto mínimo. En 3 meses faltan velas para aplicar las dos reglas con caída previa. Como antecedentes, Chen y Tsai localizan patrones con GAF, Hung y Chen aprenden representaciones de subgráficos, y Brim y Flann estudian mapas de características en otra estrategia. [Recuentos](patrones_desarrollo.csv) · [Chen y Tsai](https://arxiv.org/abs/2201.08669) · [Hung y Chen](https://doi.org/10.1371/journal.pone.0252404) · [Brim y Flann](https://doi.org/10.1371/journal.pone.0263181)

El conteo de 3 de 1.292 del sondeo inicial correspondía a la **secuencia** de doji mensual seguido de envolvente alcista diaria. En la configuración separada de 6 meses + 9 ruedas, se exige un doji en el último mes seguido de la envolvente y sus ruedas de contexto en la diaria. Aparece en **2 de 1.258** casos, CVX y XOM. Sirve para ilustrar la secuencia. El doji aislado aparece en 825 de las 1.292 vistas diarias candidatas de 9 ruedas. [Conteo de la secuencia](combinacion_patrones_desarrollo.csv) · [Casos reales](ejemplos_combinacion_patrones.csv)

## Para acordar con Simon

- Cotejar la cobertura hasta 2025, los terciles y el peso de unos pocos cortes. Definir cómo reportar la variación entre fechas y la dependencia de activos en el mismo corte. Registrar las variantes probadas. [Bailey et al.](https://escholarship.org/uc/item/4w1110bb)
- Confirmar la cadencia de estudio y los límites temporales. Llevar 6 meses + 9 ruedas y la escala relativa lineal como primera configuración. Medir primero una diferencia por vez sobre oportunidades comunes.
- En diseño temporal, auditar qué tramo de 2026 sigue disponible para evaluación y acordar costo y salida antes del entrenamiento.
