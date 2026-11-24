# ¿Cuánto aporta la vista diaria a la cartera?

Lucas es responsable del diseño, de la ejecución y de revisar las verificaciones de esta segunda iteración. La idea de sumar una vista corta al contexto procede de la propuesta oral de Gabriel. La decisión se toma al cierre de cada corte. Cada CNN recomienda comprar o guardar en efectivo la parte de capital de cada activo. La comparación principal es la diferencia, en puntos porcentuales, entre el retorno neto acumulado de mensual + diaria y el de mensual. Una diferencia positiva favorece a la primera sobre el período observado.

## Qué información llega a la decisión

El universo fijo contiene los 34 activos de la tabla del EDA. Una fila es un activo en una fecha. La CNN mensual ve los seis meses calendario completos anteriores al mes del corte. Cada vela toma primera apertura, máximo, mínimo y último cierre ajustados. La otra CNN recibe exactamente esa imagen y nueve velas diarias que terminan en el cierre del corte. Las primeras nueve ruedas del mes deben haber transcurrido. Para cada precio se calcula 100 × ln(P/P₀), con la apertura inicial de esa misma vista como P₀. Los patrones nombrados en el EDA sirven como ejemplos para clase.

## Cuándo hay una oportunidad

En el calendario común XNYS de la fuente, tomar el primer cierre del mes que permita ambas vistas y esté al menos a 20 ruedas del corte anterior. La grilla empieza en julio de 2015, cuando hay seis meses completos. Se calcula una vez sobre todo el período. Después se asigna el bloque por fecha, con la frontera superior exclusiva. Un descarte conserva el ancla de la grilla. Todos los activos de un corte van juntos. Para ser elegible, cada rueda de ambas vistas y de la tenencia debe existir y quedar en ese bloque.

| Función | Años | Fechas elegibles | Casos elegibles | Descartes desde el primer mes con historia |
|---|---|---:|---:|---|
| Entrenar pesos y ajustar escala | 2015–2020 | 65 | 2.210 | 34 por salida en 2021 |
| Elegir configuración | 2021–2022 | 17 | 578 | 204 por historia anterior y 34 por salida en 2023 |
| Elegir umbral | 2023–2025 | 29 | 986 | 204 por historia anterior y 34 por salida en 2026 |
| Evaluación retrospectiva reservada | 2026 hasta 13/11 | 4 | 136 | 204 por historia anterior y 34 sin salida en la fuente |

Cada fecha elegible conserva 34 activos. Enero–junio de 2015 antecede al arranque del calendario. El EDA ya excluía diciembre de 2025 porque la salida caía en 2026. De sus 125 fechas, se pierden otras 14 al dividir desarrollo: enero–junio de 2021 y de 2023 por historia anterior, y diciembre de 2020 y 2022 por salida posterior a la frontera. Quedan 111 fechas, 3.774 casos. El manifiesto completo incluye también diciembre de 2025 y noviembre de 2026 para explicar ambos bordes. [Tabla por motivo](../verificacion/casos_por_bloque.csv) · [Manifiesto por ID](../verificacion/manifiesto.csv)

**Qué se repite.** En meses consecutivos dos ventanas mensuales del mismo activo comparten cinco de sus seis velas. Entre los cortes admitidos hay 111 pares con cinco meses comunes (101–108 ruedas). A distancia de dos, tres, cuatro y cinco meses comparten cuatro, tres, dos y un mes respectivamente. A seis meses dejan de compartir historia mensual. Por ejemplo, julio y agosto de 2015 comparten febrero–junio. Dentro de cada ejemplo las dos frecuencias usan ruedas distintas. Entre bloques estrictos las ventanas son disjuntas. El listado de pares identifica los extremos exactos para cada activo del universo común. [Pares de fechas](../verificacion/historia_compartida.csv)

**Cuándo se libera el capital.** La operación va de la apertura de t+1 al cierre de t+20 inclusive. La separación mínima permite que una salida coincida con el cierre de decisión siguiente. Siempre ocurre antes de su apertura de entrada. Las operaciones simultáneas de los 34 activos usan fracciones distintas del mismo capital. La simulación no requiere financiar dos carteras mensuales a la vez.

## Qué se había visto

| Evidencia de la primera iteración | Qué se consultó | Uso en las decisiones |
|---|---|---|
| Nota de fuente, secciones 2–4 | Calidad de 42 series hasta el 13/11/2026, cobertura, ajustes y saltos. En 2026 figuran INTC 23/01, 24/04 y 30/10, UNH 27/01, NKE 01/04, CSCO 14/05 y el ajuste de HON del 29/06. | Ocho exclusiones por ajustes de escisiones en el historial completo. El universo de 34 y los precios ajustados tienen selección retrospectiva. |
| Base semanal, índice y gráficos de revisión | Prueba anterior con cortes 13/06, 12/09 y 12/12 de 2025, 13/03, 12/06 y 11/09 de 2026. La base ya contenía etiquetas y retornos verificados al exportar, y un gráfico de revisión de KO del 13/06/2025. El diagnóstico posterior inventarió fechas y cobertura mensual. | La auditoría revisó fechas, calidad y generación de imágenes. Una coincidencia de fechas entre iteraciones es el 13/03/2026. Otras ventanas se superponen aunque cambie el día de decisión. |
| Diagnóstico y diapositivas 25, 30–31 | En seis cortes de validación 2023–2024 se consultaron pérdidas, clases, épocas, sensibilidad al umbral y diferencias por grupo. El log loss fue 0,548292 en semanal y 0,537379 en dos vistas. La presentación dejó pendiente ejecutar prueba. | Se eligió la época 2 y se formuló la regla de cuatro de seis fechas después de ver validación. El diagnóstico motivó la nueva pregunta. |
| EDA de esta iteración | El piloto consultó resultados hasta 2025 inclusive. En 2025 entraron los cortes heredados del 13/06 y 12/09. | El EDA orientó las ventanas, la escala y la cadencia. La selección cronológica dentro de 2015–2025 sigue siendo desarrollo retrospectivo. |

Lucas confirmó que tampoco consultó resultados de modelos o carteras de 2026 fuera del repositorio. La revisión de precios de ese año sí influyó en la composición del universo. El alcance defendible es una comparación histórica condicionada a esos 34 activos. [Nota original de la fuente](https://drive.google.com/file/d/1y1QvfkneeCiFSnn6tMzzYFTCgpWjFHlQ/view) · [Base original](https://drive.google.com/file/d/1MIwe-3cN6CPsP5pfNfCaWcggt2pCSCIV/view?usp=drivesdk)

**Reserva de 2026.** Por calendario y cobertura alcanzan historia y salida para diez cortes: 14/01, 12/02, 13/03, 14/04, 13/05, 11/06, 14/07, 13/08, 14/09 y 13/10. Los seis primeros toman parte de 2025. Lucas eligió los cuatro estrictos de julio–octubre, cuyas salidas son 11/08, 11/09, 12/10 y 10/11. El 12/11 llega a la apertura siguiente pero carece de t+20. En este inventario solo se procesan claves y cobertura.

## Cómo fijar pesos y umbrales antes de prueba

1. Antes de entrenar, versionar ambas arquitecturas, resolución, límites por frecuencia y método de ajuste, optimizador, orden de lotes y presupuesto. Usar la misma rama mensual, semilla 42, procedimiento y cuatro épocas candidatas (1, 2, 4 y 8). La única extensión de la segunda arquitectura es la rama diaria y su fusión. Ajustar pesos y límites de dibujo exclusivamente con entrenamiento.
2. Para cada CNN elegir, en el bloque de configuración, el checkpoint que minimice el log loss (media dentro de fecha y luego entre fechas). En empate usar la época más temprana. Conservar esos pesos y escalas para generar las probabilidades del siguiente bloque.
3. Por separado para cada CNN, usar el bloque de umbral una sola vez para comparar la misma grilla de probabilidades: 0, 0,30, 0,40, 0,50, 0,60, 0,70 y 1,01. Cero compra siempre, 1,01 mantiene efectivo. Elegir el mayor capital final de la simulación; para un empate al redondear el capital final por unidad inicial a 12 decimales, elegir el umbral mayor. Registrar la tabla completa. El modelo compra cuando p ≥ umbral, incluida la igualdad. Los dos modelos reciben el mismo presupuesto de selección.
4. Congelar configuración, pesos, límites, umbrales, manifiesto y versión del evaluador por hash antes de abrir los resultados de 2026. Usar después exactamente estas decisiones en los cuatro cortes. Reportar cada fecha aun si ambas redes eligen efectivo. No reentrenar entre selección de umbral y prueba.
5. Para una confirmación posterior, fijar por adelantado universo, disponibilidad de precios en cada fecha, costos, reglas, comienzo y duración de un período nuevo tras la congelación. Reunir múltiples fechas y regímenes, guardar predicciones antes de t+1 y esperar la última salida t+20. Cuatro fechas con historia compartida permiten describir qué ocurrió y cuánto dependió de cada corte. Una inferencia sobre 136 ensayos independientes exageraría la evidencia.

## Cómo se calcula la cartera

Capital inicial 100, efectivo a tasa cero, sin apalancamiento, ventas cortas ni redondeo a acciones enteras. En cada fecha dividir el patrimonio líquido al cierre por el número de activos elegibles conocidos en t. Cada compra usa una de esas partes; cada pase conserva su parte en efectivo. El saldo queda líquido entre salida y apertura siguiente. La estrategia que compra siempre utiliza todas las partes; la que mantiene efectivo conserva 100.

Para cada activo, el retorno bruto es cierre ajustado de t+20 dividido por apertura ajustada de t+1 menos uno. El costo total supuesto de ida y vuelta equivale a 0,002 del capital asignado y se descuenta una vez por compra ejecutada. La etiqueta es 1 si bruto − 0,002 > 0 y 0 también cuando da exactamente cero. Se usa la misma etiqueta para ambas redes. Los dividendos ya están reflejados en el ajuste de la fuente.

El retorno del corte es la suma de retornos netos de las compras dividida por **todos** los activos elegibles. El patrimonio siguiente es el anterior multiplicado por uno más ese retorno. El retorno total es el producto de esos factores menos uno. Mostrar las cuatro curvas desde el mismo capital, diferencias en puntos porcentuales y tabla por fecha con capital inicial/final, elegibles, operaciones completas, fracción comprada y capital en efectivo. Informar además total de operaciones y exposición media (media de fracciones compradas por corte). Una fecha con cero compras tiene retorno y exposición cero. El promedio por operación solo complementa el resultado de cartera. [Ejemplo con números](ejemplo.md)

**Faltantes.** La fuente congelada tiene cobertura completa. Un dato de entrada ausente o inválido conocido en t excluye ese ID en las cuatro estrategias antes del reparto. Sin activos se conserva efectivo. Una probabilidad ausente o inválida para un ID esperado invalida la corrida. La verificación ex post de cobertura del horizonte es un control de integridad. Si una apertura o salida esperada falta sorpresivamente, detener la valoración del corte y documentar la incidencia común antes de comparar. Evitar eliminar retrospectivamente al activo, reasignar su parte o imputarle retorno cero. El final conocido de la fuente delimita qué fechas históricas pueden evaluarse.

## Qué debe demostrar el generador

- Usar el SHA-256 fijado y solo IDs elegibles del manifiesto. Reconstruir desde fechas cada rueda y verificar los dos extremos, los seis meses cerrados, las nueve ruedas, t+1, t+20 y el bloque.
- Preparar un solo PNG mensual por ID. Comparar las listas efectivas de IDs, su orden y el hash de cada PNG mensual en ambos cargadores. Rechazar duplicados, pérdidas o intercambios de filas. El control actual verifica el contrato de fechas; estos controles de archivos requieren el generador.
- Reproducir el ejemplo KO, verificar OHLC y ambos P₀. Alterar precios posteriores al corte en una copia debe dejar idénticas las dos imágenes. Ajustar los límites solo con los IDs de entrenamiento y guardar esos IDs, parámetros, resolución y recortes por bloque.
- Separar píxeles de entrada de gráficos para clase, texto, etiquetas y retornos. La caché identifica fuente, activo, corte, vista, versión del render y límites. Guardar etiquetas y resultados de prueba fuera de los insumos del generador y del ajuste.
