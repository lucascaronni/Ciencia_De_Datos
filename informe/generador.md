# Generador de imágenes · Verificación de la etapa 3

El generador usa los IDs elegibles del manifiesto en su orden original y verifica el SHA-256 del OHLC `yf20261114T2019Z` antes de procesar precios. Los controles del protocolo reconstruyeron el calendario, la separación de las vistas, t+1, t+20 y la cobertura. El manifiesto, los recuentos y el inventario de historia compartida se reprodujeron byte por byte. El gráfico histórico del calendario se volvió a dibujar con Matplotlib 3.9.4 y difiere en píxeles del original, generado con 3.9.2. [Comando para reproducir](../README.md#reproducir-las-imágenes) · [Manifiesto](../verificacion/manifiesto.csv)

| Bloque | Cortes | Esperados | Cargador mensual | Cargador de dos vistas | PNG mensuales idénticos |
|---|---:|---:|---:|---:|---:|
| Entrenamiento | 65 | 2.210 | 2.210 | 2.210 | 2.210 |
| Configuración | 17 | 578 | 578 | 578 | 578 |
| Umbral | 29 | 986 | 986 | 986 | 986 |
| Retrospectiva reservada | 4 | 136 | 136 | 136 | 136 |
| **Total** | **115** | **3.910** | **3.910** | **3.910** | **3.910** |

Ambos cargadores decodificaron el lote y coincidieron con el manifiesto ID por ID, en el mismo orden. Comparten una única ruta mensual por ID y el contenido tiene el mismo SHA-256 en los dos cargadores. Los 7.820 PNG de entrada son RGB de 192 × 192, con el fondo y las velas como únicos elementos. Los cargadores devuelven un arreglo `uint8` de forma `(192, 192, 3)` por vista, sin redimensionado. Keras 3.10.0 leyó los dos PNG de KO con igualdad exacta de píxeles frente al cargador del lote. [Recuentos y hashes ordenados](../verificacion/imagenes/controles.json) · [Cargadores](../src/cargar_imagenes.py) · [Lectura de imágenes en Keras](https://keras.io/api/data_loading/image/)

## Del precio a la fila de la imagen

Cada vela mensual usa la primera apertura, el máximo de máximos, el mínimo de mínimos y el último cierre ajustados del mes. Se toman seis meses calendario cerrados. La diaria toma las nueve ruedas ajustadas hasta el corte inclusive. La última rueda mensual precede a la primera diaria en todos los casos.

Para cada precio ajustado `P`, el eje vertical de la figura para clase representa `z = 100 × ln(P/P₀)`, donde `P₀` es la primera apertura de esa vista. `z = 0` equivale a `P = P₀`. Una unidad de `z` equivale a multiplicar el precio por `exp(0,01)`, aproximadamente un 1,005 %. En el PNG, las subas van hacia filas menores.

Se ajustaron dos rangos centrales fijos, uno por vista, con el percentil 0,5 de los mínimos y el 99,5 de los máximos transformados de los 2.210 IDs de entrenamiento. El registro contiene esos IDs en el orden del manifiesto y la configuración conserva las huellas de la fuente, el manifiesto, los parámetros del render y el archivo de IDs. [Rangos y huellas](../config/escalas_imagenes.json) · [IDs de ajuste](../verificacion/imagenes/ids_ajuste.txt) · [Configuración del render](../config/render.json)

| Vista | Rango central en unidades de `z` | Píxeles por unidad en el tramo central |
|---|---:|---:|
| Mensual | −59,078 a 43,054 | 1,557 |
| Diaria | −16,900 a 16,205 | 4,803 |

El tramo central es lineal y va de la fila 16 a la 175. Dentro de él una variación `Δz` ocupa `|Δz| × píxeles por unidad`. Cada extremo tiene 12 filas adicionales. Si un punto sale del rango central en una distancia que ocuparía `d` píxeles con la pendiente central, se asigna `12 × d/(12+d)` píxeles desde el extremo del tramo, hacia arriba o abajo. Se conserva el orden de los precios y la altura se comprime gradualmente. Para una mecha o cuerpo que atraviese tramos, la altura es la distancia entre las dos coordenadas convertidas.

En la primera revisión, el render lineal con corte en los percentiles saturaba el 5,27 % de las velas mensuales de 2026. Se sustituyó ese corte por compresión gradual. La resolución, los rangos centrales y el espacio para los extremos se decidieron con entrenamiento. A 192 × 192, se probaron 10, 12, 16 y 20 filas por extremo. Con 10 filas, dos velas diarias de entrenamiento caían en la fila exterior del área de dibujo. Con 12, ninguna llegaba a esa fila y se conservaba más detalle central que con 16 o 20. Las métricas de 2026 se usaron para revisar el comportamiento de los píxeles. [Implementación de la escala](../src/render_velas.py)

Se redondean las coordenadas a la fila más cercana. Si apertura y cierre caen en la misma fila, el cuerpo ocupa una fila de alto y nueve píxeles de ancho. La línea de máximo a mínimo mide un píxel de ancho. Una mecha muy corta puede caer en la fila del cuerpo y dejar de distinguirse. Los porcentajes de altura inferior a un píxel se miden tras la conversión continua y antes del redondeo o del grosor mínimo. Incluyen longitudes cero. El CSV separa mechas superiores e inferiores y registra cuántos cuerpos terminan en una sola fila.

| Bloque | Vista | Velas recortadas | Velas que usan compresión | Cuerpos < 1 px | Mechas < 1 px |
|---|---|---:|---:|---:|---:|
| Entrenamiento | Mensual | 0 | 1,01 % | 9,28 % | 18,66 % |
| Entrenamiento | Diaria | 0 | 1,01 % | 18,20 % | 31,51 % |
| Configuración | Mensual | 0 | 1,01 % | 8,16 % | 20,43 % |
| Configuración | Diaria | 0 | 0,27 % | 14,34 % | 24,83 % |
| Umbral | Mensual | 0 | 0,83 % | 8,55 % | 20,18 % |
| Umbral | Diaria | 0 | 1,03 % | 16,41 % | 28,45 % |
| Retrospectiva | Mensual | 0 | 5,27 % | 10,91 % | 17,83 % |
| Retrospectiva | Diaria | 0 | 1,47 % | 14,54 % | 25,65 % |

Ninguna vela llegó a las filas exteriores del área de dibujo. En 2026, la compresión afecta a 15 de las 136 imágenes mensuales y a 6 de las 136 diarias. Las métricas describen resolución y geometría de las entradas. El resultado del aprendizaje queda para la etapa siguiente. [Métricas por bloque y vista](../verificacion/imagenes/metricas.csv)

## KO al 14 de julio de 2015

Las seis velas mensuales cubren enero a junio y usan `P₀ = 29,299129 USD`. Las nueve velas diarias corresponden al 1, 2, 6, 7, 8, 9, 10, 13 y 14 de julio, con `P₀ = 27,756065 USD`. El cierre diario final es 29,017696 USD. Una reconstrucción independiente desde el CSV confirmó los OHLC y los valores transformados de las 15 velas. El PNG mensual es el archivo compartido por las dos CNN. La figura amplía el eje para que se distingan las velas en clase. [Figura explicada](../verificacion/imagenes/KO_2015-07-14_explicado.png) · [PNG mensual](../verificacion/imagenes/KO_2015-07-14_mensual.png) · [PNG diario](../verificacion/imagenes/KO_2015-07-14_diaria.png) · [Precios ajustados y valores transformados](../verificacion/imagenes/KO_2015-07-14_velas.csv)

## Controles de disponibilidad y caché

En copias en memoria se multiplicó por 1,37 cada OHLC posterior al corte de KO para el 14/07/2015, el 14/07/2026 y el 13/10/2026. Se alteraron 2.852, 87 y 23 ruedas, respectivamente. Con los límites congelados y la caché desactivada, los hashes de ambas vistas coincidieron entre la serie original, la alterada y la truncada al corte. Los hashes originales también coincidieron con los del lote. Como control de sensibilidad, multiplicar por 1,05 el OHLC de la propia rueda del 14/07/2015 cambió el hash diario y conservó el mensual. La carga normal rechazó un CSV de control con SHA-256 distinto.

Los cuatro cortes reservados son el 14/07, 13/08, 14/09 y 13/10 de 2026, con 34 activos cada uno. Las 136 entradas se prepararon usando precios hasta el cierre de su corte. En ese bloque se trabajó con calendario, cobertura y píxeles. Las etiquetas, predicciones y resultados económicos siguen reservados. [Cortes y hashes del control](../verificacion/imagenes/controles.json)

La clave local incluye versión y SHA-256 de la fuente, activo, corte, vista, parámetros efectivos, huella del código de render, versión del codificador y huella de los OHLC transformados. Se compararon dos lotes completos, uno desde una caché vacía y otro con lectura de caché deshabilitada. Coincidieron los bytes de los 7.820 PNG y del índice. Una tercera pasada leyó los 7.820 PNG desde la caché. Los hashes publicados corresponden al entorno de verificación con Python 3.9.6 y las dependencias fijadas. La compresión PNG y el gráfico de clase pueden variar en otros entornos.

Para la etapa siguiente, las mechas y los cuerpos muy cortos limitan los patrones que puede distinguir la CNN, especialmente en la vista diaria. En los extremos, dos variaciones logarítmicas de la misma magnitud pueden ocupar alturas distintas según su posición. Además, los cortes cercanos del mismo activo comparten historia mensual dentro de cada bloque. La retrospectiva tiene cuatro fechas y usa el universo fijo seleccionado a partir de la fuente ajustada. [Protocolo y alcance de la comparación](protocolo.md)
