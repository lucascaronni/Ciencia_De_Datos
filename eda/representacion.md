# EDA y representación · Desarrollo 2015–2025

La comparación posterior medirá si sumar velas diarias a las mensuales mejora el retorno neto de comprar o quedarse en efectivo en las mismas oportunidades. Para este EDA se usó el calendario de cortes de la primera iteración. Se ampliaron las fechas de desarrollo hasta el 31/12/2025 y se recalcularon los retornos desde el OHLC congelado. Los datos de 2026 quedan fuera del análisis. Su eventual uso para evaluación requiere comprobar qué fechas ya se consultaron en la primera iteración.

## Universo y concentración

El CSV tiene **2.766 ruedas** por activo para los **34 activos de 11 sectores**, del 02/01/2015 al 31/12/2025. Hay 39 cortes candidatos de 34 activos cada uno. Quedan 38 cortes y 1.292 operaciones tras excluir el 12/12/2025, cuyo horizonte t+20 rebasa desarrollo. El calendario heredado ofrece dos cortes elegibles en 2025. [Activos](activos_desarrollo.csv) · [Cortes y exclusiones](cortes_desarrollo.csv)

Las cifras usan apertura ajustada de t+1, cierre ajustado de t+20 y **costo total supuesto de 0,20 %**. Bajo ese piloto, 804 de 1.292 operaciones (62,2 %) fueron positivas y el retorno neto medio fue +2,51 %. El 20/03/2020 alcanzó +26,41 % de media con 34 de 34 positivos. Ese corte, el 25/09/2015 y el 21/12/2018 suman 36,1 % de los retornos medios de los cortes con media positiva. Si se retiran los tres como sensibilidad descriptiva, la media baja a +1,46 %. El mínimo fue −6,29 % el 24/12/2015. Los mínimos de proporción positiva (6 de 34) se dieron el 16/09/2022 y el 15/09/2023. [Figura temporal](resultados_por_fecha_desarrollo.png) · [Tabla](resultados_por_fecha_desarrollo.csv) · [Operaciones](operaciones_desarrollo.csv)

La volatilidad histórica va de 17,8 % a 39,1 %. El gráfico por fecha anualiza el desvío de los últimos 20 retornos diarios al corte por activo y promedia los activos. Los terciles bajo, medio y alto tienen 11, 12 y 11 activos y 58,1 %, 67,3 % y 60,8 % de operaciones positivas bajo el mismo piloto. Materiales básicos, comunicaciones e inmobiliario tienen dos activos cada uno. Todo consumo defensivo queda en el tercil bajo. De las 33 celdas sector × tercil, 10 están vacías y 16 tienen un solo activo. Simon debe cotejar la clasificación, los terciles recalculados y la representatividad por grupo y fecha. La selección del universo y el ajuste de precios de Yahoo son retrospectivos. [Mapa de cobertura](sectores_y_volatilidad.png) · [Sector](resultados_por_sector_desarrollo.csv) · [Tercil](resultados_por_tercil_desarrollo.csv) · [Cruce](resultados_por_sector_y_tercil_desarrollo.csv)

## Ventanas y muestra común

| Candidata | Casos | Fechas | Activos | Pares consecutivos de fechas con ruedas compartidas |
|---|---:|---:|---:|---:|
| 3 meses cerrados | 1.292 | 38 | 34 | 0 de 37 |
| 6 meses cerrados | 1.258 | 37 | 34 | 34 de 36 |
| 5 ruedas | 1.292 | 38 | 34 | 0 de 37 |
| 10 ruedas | 1.292 | 38 | 34 | 0 de 37 |
| 20 ruedas | 1.292 | 38 | 34 | 0 de 37 |
| Intersección de las cinco | 1.258 | 37 | 34 | Depende de la vista |

Cada oportunidad es un activo y corte con las ruedas completas según el calendario de desarrollo del CSV. La vela mensual toma apertura inicial, máximo, mínimo y cierre final. Excluye el mes del corte. La vista diaria incluye el corte. En 6 meses se pierden los 34 casos del 26/06/2015 porque faltaría diciembre de 2014. Se comparten hasta 65 ruedas entre cortes consecutivos de un mismo activo. [Recuentos](cobertura_ventanas_desarrollo.csv) · [Claves elegibles por candidata](elegibilidad_ventanas_desarrollo.csv)

En KO al **12/09/2025**, tres meses muestran junio–agosto y seis añaden marzo–mayo. Las cinco ruedas empiezan el 08/09, las diez el 29/08 y las veinte el 15/08. Las diez comparten el 29/08 con la mensual. En todo desarrollo, 5 ruedas comparte 0 días entre vistas, 10 comparte una rueda en 68 casos (13/09/2024 y 12/09/2025), y 20 comparte hasta 11 en 1.258 casos de 37 fechas. La información compartida ya existía al corte. [Figura de KO](ventanas_KO.png) · [Cruces entre vistas](combinaciones_ventanas_desarrollo.csv)

**Para revisar.** Probar primero **3 meses frente a 3 meses + 10 ruedas** conserva los 1.292 casos y aporta más detalle reciente que 5 ruedas. Si el equipo quiere vistas sin ruedas compartidas en ningún corte, 5 ruedas conserva la cobertura. Evaluar 6 meses requiere usar las 1.258 oportunidades comunes y acordar cómo tratar el solapamiento entre cortes. El rendimiento predictivo y económico se mide después.

## Escalas sobre las mismas velas

| Escala | Qué muestran cuerpos, mechas y amplitud |
|---|---|
| Precio ajustado | Distancias y amplitud en USD ajustados. |
| Log natural | Distancias logarítmicas, equivalentes al logaritmo de razones. Conserva orden y dirección. Un mismo cambio en USD ocupa menos altura cuanto mayor sea el precio, por lo que puede cambiar la proporción entre cuerpo y mechas. El log numérico es reversible. |
| Min–max por vista | Un mismo mínimo Low y máximo High para los cuatro campos. Preserva proporciones y dirección dentro de la vista. Todas las amplitudes pasan a 1 y se pierden el nivel y la amplitud originales si solo se guarda la imagen normalizada. Un extremo puede comprimir las demás velas. |

Al 12/09/2025, los rangos en 3 meses y 10 ruedas son **4,55 y 2,44 USD en KO** (volatilidad baja, 17,8 %), **22,73 y 12,60 en UNP** (media, 25,3 %) y **14,34 y 8,86 en COP** (alta, 38,0 %). En COP, la mecha inferior de agosto mide 3,62 USD y el cuerpo 4,66 USD. En log pasan a 0,04041 y 0,04979, por lo que la relación mecha/cuerpo cambia de 0,78 a 0,81. [KO](escalas_KO.png) · [UNP](escalas_UNP.png) · [COP](escalas_COP.png) · [Medidas](medidas_escalas_desarrollo.csv)

Los ejes se ajustan a cada panel para inspección. En imágenes sin ejes, el autoajuste por ventana puede volver equivalentes el precio lineal y el min–max en píxeles. El renderizado debe fijar límites, tamaño y márgenes. `keras.layers.Rescaling(1/255)` actúa después del dibujo sobre intensidades RGB, conserva la posición de los píxeles y cumple otra función. La elección de escala sigue abierta. Con los apuntes de modelado estocástico queda por revisar si interesa preservar amplitudes entre cortes, cómo tratar cambios de nivel y de volatilidad, y qué supuestos justifican trabajar con diferencias logarítmicas. El log de niveles por sí solo no garantiza estacionariedad. [Documentación de Keras](https://keras.io/api/layers/preprocessing_layers/image_preprocessing/rescaling/)

## Patrones OHLC

`B = |C − O|` es el cuerpo, `R = H − L` el rango y las mechas son `H − max(O,C)` y `min(O,C) − L`. La caída previa se operacionaliza como tres cierres consecutivos descendentes hasta la vela anterior al disparo. En la envolvente, el tercero es el de la primera vela del patrón. Se exige que todo el contexto esté visible. Los umbrales numéricos son del EDA.

| Patrón | Regla sobre OHLC ajustado | Casos entre 1.292 vistas de 10 ruedas |
|---|---|---:|
| Doji | `R > 0` y `B ≤ 0,10 × R`. | 871, en 38 fechas y 34 activos. [Ponsi, cap. 14](https://onlinelibrary.wiley.com/doi/10.1002/9781119204800.ch14) |
| Martillo | Caída previa, `B > 0`, mecha inferior ≥ `2 × B` y superior ≤ `0,10 × R`. | 53, en 25 fechas y 28 activos. [Ponsi, cap. 13, p. 144](https://onlinelibrary.wiley.com/doi/10.1002/9781119204800.ch13) · [Manual, p. 25](https://drive.google.com/file/d/1zz5J7nYJ4EPZVtIJVCf-_pt9IVoK_K4J/view) |
| Envolvente alcista | Caída previa, primera vela bajista y segunda alcista, `O₂ < L₁`, `H₂ > H₁` y `C₂ > O₁`. Variante estricta de rango completo. | 25, en 16 fechas y 17 activos. [Ponsi, cap. 13, figs. 13.7–13.8](https://onlinelibrary.wiley.com/doi/10.1002/9781119204800.ch13) |

Los conteos son casos con alguna ocurrencia visible. El CSV incluye la presencia en la última vela y el contexto mínimo. En 3 meses faltan velas para aplicar las dos reglas con caída previa. Como antecedentes, Chen y Tsai localizan patrones con GAF, Hung y Chen aprenden representaciones de subgráficos, y Brim y Flann estudian mapas de características en otra estrategia. [Recuentos](patrones_desarrollo.csv) · [Chen y Tsai](https://arxiv.org/abs/2201.08669) · [Hung y Chen](https://doi.org/10.1371/journal.pone.0252404) · [Brim y Flann](https://doi.org/10.1371/journal.pone.0263181)

Se sondeó **doji en el último mes cerrado y luego envolvente alcista en las últimas 10 ruedas**, exigiendo que las cuatro ruedas de contexto diario sean posteriores al mes. Apareció en **3 de 1.292 casos**, en CVX, HD y XOM. Queda como ilustración para clase por su baja frecuencia. Los patrones individuales sirven para anotar ejemplos. [Conteo](combinacion_patrones_desarrollo.csv) · [Casos reales](ejemplos_combinacion_patrones.csv)

## Para acordar con Simon

- Cotejar la cobertura hasta 2025, los terciles y el peso de unos pocos cortes. Definir cómo reportar la variación entre fechas y la dependencia de activos en el mismo corte. Registrar las variantes probadas. [Bailey et al.](https://escholarship.org/uc/item/4w1110bb)
- Elegir 5 o 10 ruedas para la primera comparación y acordar el tratamiento del cruce si se usa 10. Cotejar las escalas con los apuntes y fijar límites de renderizado.
- En diseño temporal, auditar qué tramo de 2026 sigue disponible para evaluación y acordar costo y salida antes del entrenamiento.
