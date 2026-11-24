# Primer control visual de las ventanas

El corte del 16/09/2022 pertenece a desarrollo. Los tres activos sirven como ejemplos concretos de los terciles de volatilidad. KO pertenece a consumo defensivo, UNP a industria y COP a energía. Cada figura usa junio, julio y agosto en la fila mensual y las últimas diez ruedas hasta el corte en la diaria.

- **Precio ajustado.** El eje conserva precio y amplitud en dólares ajustados.
- **Log natural.** Conserva el orden y la dirección de las velas. Las distancias entre niveles expresan diferencias logarítmicas. Con rendimientos chicos, la forma suele verse parecida.
- **Min–max por ventana.** Conserva las relaciones lineales entre cuerpos y mechas dentro de la misma vista. Al pasar el rango de cada ventana a 0–1, se pierde la posibilidad de leer la amplitud original comparando dos gráficos normalizados.

Las figuras son material de revisión. Sus ejes se ajustan a cada panel y los PNG para entrenar necesitan una especificación de renderizado aparte. La comparación visual permite revisar el efecto de la transformación. La elección de escala queda abierta hasta el EDA y la revisión del protocolo.
