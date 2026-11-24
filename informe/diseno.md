# Diseño del experimento

## Pregunta de negocio

**¿Incorporar velas diarias recientes a una CNN basada en velas mensuales mejora, para las mismas oportunidades de inversión, el retorno neto de una estrategia simulada que decide cuándo comprar y cuándo mantener el capital en efectivo?**

La primera comparación mide el aporte de lo diario. Las referencias económicas son comprar en cada oportunidad bajo la misma asignación y quedarse en efectivo. Se puede mantener la CNN semanal original como antecedente de la primera iteración.

## Qué ve la red y qué predice

Una oportunidad es un activo y una fecha de corte. La predicción se produce después del cierre de ese día. Las vistas candidatas tienen 3 o 6 meses calendario completos anteriores al mes del corte y 5, 10 o 20 ruedas diarias hasta el corte. El EDA y la selección en desarrollo y validación definen qué ventanas llegan a la comparación final.

El piloto usa una orden de compra en la apertura de la rueda t+1 y una salida al cierre de t+20. Calcula el retorno simple ajustado de la operación menos un costo total supuesto de 0,20 % del capital asignado. La etiqueta piloto vale 1 si ese retorno neto es mayor que cero. Los costos y la salida a 20 ruedas se usan para medir factibilidad. Antes de cerrar la especificación se documentarán el supuesto de costos, la regla de salida y, si aplica, el retorno mínimo que justifica la operación. El cierre ajustado mide retornos con distribuciones reflejadas por la fuente.

La CNN devuelve una probabilidad de que la etiqueta sea 1. La regla simulada transforma esa probabilidad en comprar o mantener en efectivo la asignación de esa oportunidad. Se selecciona con datos de desarrollo y validación porque la probabilidad de una ganancia y la magnitud del retorno son distintas.

## Cómo se mide la decisión

Armar una cartera con igual peso por activo elegible en cada fecha de decisión. La fracción asignada a un activo que se decide pasar queda en efectivo a tasa cero en el piloto. Para comparar estrategias, usar las mismas fechas, activos, capital disponible, ejecución y costos. Las fechas del piloto están separadas unas trece semanas y las operaciones de veinte ruedas terminan antes de la siguiente. Si se cambia la cadencia, se debe especificar la asignación cuando se solapen posiciones.

Reportar retorno neto de cartera por fecha y acumulado, exposición y cantidad de operaciones. La pérdida logarítmica y las métricas por clase responden una pregunta complementaria sobre las probabilidades. Una ventaja en el promedio por operación elegida puede convivir con una ganancia menor para toda la cartera.

## Ventanas y evaluación temporal

El EDA de esta iteración usa desarrollo de **2015 a 2025 inclusive**. El calendario de cortes se toma del índice anterior. Se aplica la nueva frontera por fecha y se exige que la historia de las entradas, la apertura t+1 y el cierre t+20 queden en desarrollo. Las comparaciones de longitudes se hacen sobre oportunidades comunes. [Cobertura, escalas y patrones](../eda/representacion.md)

La ampliación incorpora años que la primera iteración había asignado a evaluación. En la segunda iteración, 2026 queda fuera del EDA y como reserva para diseñar la evaluación. Antes de fijar validación y prueba, verificar qué cortes de 2026 ya se consultaron en la primera iteración y si queda un período independiente con cobertura suficiente. Si se reutilizan fechas examinadas, presentar su evaluación como retrospectiva.

La selección de ventana, etiqueta, umbral, escala y arquitectura precede a la puntuación de prueba. Guardar un manifiesto por decisión con ID, activo, inicio de vistas, corte, fecha de entrada, fecha de salida, bloque y referencia a los datos. Verificar que las entradas y el horizonte de cada ejemplo queden dentro del bloque asignado.

## De los datos a una comparación que se pueda explicar

1. Completar el EDA de retornos por fecha y grupo, conteo de patrones y sensibilidad de escalas. Contrastar precio lineal, logaritmo y min–max sobre las mismas ventanas, incluyendo amplitud y formas que cada representación conserva.
2. Fijar el diseño. Acotar candidatos de ventanas y cualquier combinación de patrones. Cada patrón nombrado necesita una regla en OHLC, una fuente y suficientes ocurrencias para compararlo.
3. Implementar el generador desde el CSV congelado, con caché local por fuente, activo, corte, vista y parámetros. Separar el gráfico explicativo de los píxeles que entran a la red.
4. Entrenar comparadores sencillos y CNN mensual y mensual + diaria. En cada comparación modificar una decisión con las demás fijas y registrar datos, configuración, pesos y métricas.
5. Mostrar la decisión y el resultado con un ejemplo reproducible. La demo futura puede presentar corte, dos vistas, probabilidad y decisión. Para cortes históricos, el retorno se revela después de la predicción.

El README enlaza el código, las figuras y las tablas derivadas del EDA. Los insumos originales se identifican por ruta y versión.

## Extensión posterior · noticias

Si queda tiempo después de evaluar la estrategia, seleccionar con una regla explícita algunos casos de retorno extremo o de error de predicción alto. Documentar qué noticias financieras identificamos, sus fuentes y sus horas de publicación. Contrastar si cada noticia estaba disponible al momento del corte o apareció después. La revisión sirve para contextualizar los casos. Una coincidencia de fechas por sí sola es insuficiente para atribuir el movimiento a la noticia.

Si se prueba información externa como entrada, usar solo publicaciones disponibles hasta la decisión, congelar las reglas de obtención y comparar la nueva variante en un período reservado. Eso constituye otro experimento.
