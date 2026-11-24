# Guía breve para la defensa oral

**Recorrido sugerido de cinco minutos.** Abrí el [informe final](informe_final.md). Tené a mano los [dos PNG de KO](evaluacion_2026.md#caso-ko) y la [curva de capital](../verificacion/etapa_4/capital_acumulado.png).

| Tiempo | Qué mostrar | Qué decir con tus palabras |
|---|---|---|
| 0:00–0:45 | La pregunta | «Gabriel propuso comparar contexto y detalle reciente. En la primera iteración, sumar diez ruedas a trece semanas redujo la pérdida logarítmica de validación, pero a 0,50 la doble no señaló ningún positivo. En la segunda quise medir qué cambia en el dinero si la estrategia puede comprar o esperar». |
| 0:45–1:30 | [Ventanas](../eda/ventanas_KO.png) | «Usé los mismos 34 activos en ambas redes. Seis meses cerrados daban medio año de contexto. Nueve ruedas agregaban detalle reciente sin repetir ruedas de esos meses. Con diez ya había 68 cruces en el piloto». |
| 1:30–2:45 | Los dos PNG de KO | «En julio de 2026 la primera imagen resume enero a junio y la segunda muestra las nueve ruedas hasta el 14 de julio. El log relativo convierte precios en movimientos comparables. Keras divide los colores por 255. La mensual resume su imagen en 16 rasgos. La doble agrega 8 de la diaria antes de estimar la probabilidad de que la compra termine en positivo después del costo». |
| 2:45–3:30 | [Los cuatro bloques](informe_final.md#cuatro-bloques-con-funciones-distintas) | «2015–2020 ajustó pesos y escalas. 2021–2022 eligió la época por pérdida logarítmica. 2023–2025 eligió el umbral por capital final. Con todo eso fijo, apliqué la regla en cuatro fechas de 2026». |
| 3:30–4:15 | [Operación de KO](../verificacion/etapa_4/caso_ko.json) | «La mensual dio 0,5291 y la doble 0,5940. Las dos cruzaron 0,50 y compraron la misma fracción, 100/34. KO rindió +4,0807 % neto y aportó 0,1200 unidades a la cartera». |
| 4:15–5:00 | La curva de capital | «Las redes compraron las 136 oportunidades, incluso en los dos cortes con pérdidas. Desde 100 terminaron en 103,3511, exactamente como comprar siempre. Efectivo conservó 100. En estos cuatro cortes, con este universo y esta regla, agregar la vista diaria aportó cero puntos porcentuales». |

## Preguntas para practicar sin leer

1. **¿Por qué la red aprendió a dar probabilidades?** Cada imagen de entrenamiento tenía una etiqueta 1 o 0 según si la compra ganaba después del costo. La sigmoide daba un valor entre 0 y 1. La entropía cruzada penalizaba la confianza alta en la etiqueta equivocada y el optimizador ajustaba los pesos. Un 0,5940 estima la probabilidad del evento. El porcentaje de ganancia se calcula luego con los precios de ejecución.
2. **¿Cómo pasó esa probabilidad a una decisión?** Al cierre del corte se comparó con el umbral congelado. Con p ≥ 0,50 se compraba en la próxima apertura. Por debajo se guardaba esa fracción en efectivo. Una vez decidida la compra, el importe era el mismo por activo, cualquiera fuera la probabilidad.
3. **¿Por qué quedó 0,50?** En 2023–2025, cuatro umbrales empataron en el máximo capital final. El desempate previsto eligió el mayor. Aplicar otro umbral después de conocer 2026 sería plantear otro experimento. [Grilla de selección](../verificacion/etapa_3b/seleccion_umbral.csv)
4. **¿Qué significa el empate contra comprar siempre?** A las 136 compras de la referencia, cada red les asignó exactamente las mismas fechas, posiciones y costos. Las carteras ganaron lo mismo por construcción. Las 69 compras positivas ayudan a distinguir «compró» de «acertó». Las pérdidas de agosto y septiembre también entraron en el acumulado.
5. **Si las carteras empataron, ¿qué distingue a las redes?** A la mensual le fue mejor en log loss (0,6964 frente a 0,7254). Esa métrica usa el valor de cada probabilidad. Para la cartera bastaba con estar de un lado u otro de 0,50. [Métricas](../verificacion/etapa_4/metricas.json)
6. **¿Qué estuvo reservado y qué limita la conclusión?** Se reservaron los resultados económicos, etiquetas y predicciones de esta comparación. La inspección previa de los píxeles de 2026 influyó en el cambio de render. El universo se seleccionó retrospectivamente y dos cortes consecutivos comparten cinco meses. La confirmación requeriría más fechas en un período futuro definido de antemano.

**Ensayo final.** Tapá la curva y explicá cómo puede haber a la vez dos probabilidades distintas, dos meses con pérdidas y tres carteras con el mismo saldo final. Después comprobá tu respuesta en la [tabla de las cuatro estrategias por fecha](evaluacion_2026.md#las-cuatro-decisiones-mensuales).
