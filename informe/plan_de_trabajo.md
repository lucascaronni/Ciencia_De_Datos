# Plan de trabajo · Iteración 2

Lucas lleva adelante la segunda iteración y resuelve las decisiones abiertas. Lucas revisa los controles y registra sus decisiones y traspasos en Git. Los chats de trabajo usan el mismo repositorio. Cada uno arranca con la ruta o URL del repositorio, el último commit pertinente, los archivos que puede modificar y la pregunta que debe resolver.

| Chat | Tareas | Entrega | Modelo recomendado |
|---|---|---|---|
| EDA y representación | Revisar cobertura, sectores y volatilidad. Comparar ventanas, escalas y patrones sobre los mismos cortes de desarrollo. | Figuras, tablas y recomendación razonada sobre qué ventanas y escalas probar. | 6.2 Sol |
| Diseño y evaluación temporal | Documentar la etiqueta, simulación, universo y fronteras que revisa Lucas. | Protocolo con decisiones, supuestos, comparadores y criterio para reservar prueba. | 6.2 Astra |
| Código y experimento | Implementar el generador y las dos CNN. Verificar el manifiesto de fechas, las entradas y las referencias de inversión. | Una ejecución reproducible con parámetros, resultados y figuras. | 6.2 Sol |
| Resultados e informe | Preparar el relato y las figuras. Cotejar cifras, fuentes y el alcance de la conclusión. | Informe con la pregunta de negocio, el método, los resultados y sus límites. | 6.2 Astra para revisar conclusiones y 6.2 Sol para edición |
| Demo en Vercel | Preparar la interfaz y verificar un recorrido histórico desde corte e imágenes hasta decisión y resultado. | Demo que identifica si ejecuta inferencia o muestra resultados previamente calculados. | 6.2 Sol |

## Primer bloque · EDA y representación

El EDA de 2015–2025 dejó definida la primera comparación de 6 meses cerrados frente a 6 meses cerrados + 9 ruedas separadas, con log relativo. La [nota del EDA](../eda/representacion.md) reúne las verificaciones y los resultados. Lucas fijó la cadencia, la etiqueta, la simulación y los cuatro bloques en el [protocolo](protocolo.md). El siguiente chat implementa el generador y comprueba imágenes e IDs antes de entrenar.

## Cierre de cada chat

Entregar los enlaces a archivos y commits, qué se verificó y qué queda pendiente. Avisar **LISTO PARA REVISIÓN** cuando la entrega esté completa. Consultar a Lucas las decisiones que cambien el alcance o los criterios de evaluación y registrar en el repositorio las que habiliten el siguiente bloque.

En GitHub quedan el código, los parámetros, las fechas de bloques, el informe, los datos resumidos y las figuras reproducibles. Los insumos pesados se identifican por versión y ruta de origen. Las imágenes de entrada se pueden regenerar con el generador y guardar temporalmente en caché local.
