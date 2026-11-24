# Plan de trabajo · Iteración 2

El Chat General registra acuerdos y traspasos. Los chats de trabajo usan el mismo repositorio. Cada uno arranca con la ruta o URL del repositorio, el último commit pertinente, los archivos que puede modificar y la pregunta que debe resolver.

| Chat | Responsable y tareas relacionadas | Entrega | Modelo recomendado |
|---|---|---|---|
| EDA y representación | Simon revisa cobertura, sectores y volatilidad. Lucas compara velas mensuales y diarias, escalas y patrones candidatos. Usan los mismos datos y cortes de desarrollo. | Figuras, tablas y recomendación razonada sobre qué ventanas y escalas probar. | 6.2 Sol |
| Diseño y evaluación temporal | Lucas y Simon revisan juntos la etiqueta, la simulación, el manejo de efectivo, el universo de activos y los límites de cada bloque. | Protocolo con decisiones, supuestos, comparadores y criterio para reservar prueba. | 6.2 Astra |
| Código y experimento | Lucas implementa el generador y las dos CNN. Simon revisa el manifiesto de fechas, las entradas y las referencias de inversión. | Una ejecución reproducible con parámetros, resultados y figuras. | 6.2 Sol |
| Resultados e informe | Lucas prepara el relato y las figuras. Simon coteja cifras, fuentes y el alcance de la conclusión. | Informe con la pregunta de negocio, el método, los resultados y sus límites. | 6.2 Astra para revisar conclusiones y 6.2 Sol para edición |
| Demo en Vercel | Lucas ensambla la interfaz. Simon verifica un recorrido histórico desde corte e imágenes hasta decisión y resultado. | Demo que identifica si ejecuta inferencia o muestra resultados previamente calculados. | 6.2 Sol |

## Primer bloque · EDA y representación

El bloque usa 2015–2025 para comparar ventanas, escalas y patrones OHLC. Simon coteja cobertura, grupos y concentración por fecha. Lucas y Simon revisan la propuesta inicial de entradas en la [nota con los resultados](../eda/representacion.md). El diseño de validación y prueba se resuelve en el bloque de evaluación temporal.

## Cierre de cada chat

Entregar los enlaces a archivos y commits, qué se verificó y qué queda pendiente. Avisar **LISTO PARA REVISIÓN CONJUNTA** cuando la entrega esté completa. Lucas y Simon registran en el repositorio la decisión que habilita el siguiente bloque.

En GitHub quedan el código, los parámetros, las fechas de bloques, el informe, los datos resumidos y las figuras reproducibles. Los insumos pesados se identifican por versión y ruta de origen. Las imágenes de entrada se pueden regenerar con el generador y guardar temporalmente en caché local.
