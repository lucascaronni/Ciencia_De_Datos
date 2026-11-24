# Reproducción y traspaso de 3B

## Verificar la entrega en el workspace

Ejecutar desde la raíz de `iteracion_2`. La corrida usó Python 3.9.6 en macOS arm64, Keras 3.10.0, JAX 0.4.30 en CPU y precisión `float32`. Usar las dependencias fijadas y conservar la caché de 3A. El índice apunta a la caché mediante rutas relativas. [Dependencias](../requirements-cnn.txt) · [Entorno y controles reales](../verificacion/etapa_3b/entrenamiento.json)

```bash
source .venv/bin/activate
python -m pip install -r requirements-cnn.txt
export KERAS_BACKEND=jax JAX_PLATFORMS=cpu
ohlc_iteracion2='../entregables/02 — Base semanal/OHLC_diario_yf20261114T2019Z.csv'

python src/seleccionar_3b.py "$ohlc_iteracion2" --verificar
```

La verificación valida los SHA-256 de fuente, índice, código, manifiesto, escalas, pesos y archivos locales. En los tres bloques de 3B vuelve a cotejar los PNG con 3A, recarga ambas redes y compara sus probabilidades por ID con las guardadas. El error absoluto máximo observado fue 0 en los seis archivos, con una tolerancia fijada de `1e-6`. En el bloque de umbral se comprueba además la igualdad de las decisiones para cada candidato. La simulación reconstruye las etiquetas del bloque, repite la grilla fijada y exige los mismos umbrales, tablas, métricas y ejemplo. La verificación conserva el estado de la entrega. [Regla y huellas](../config/congelado_3b.json)

## Replicar el procedimiento en otra carpeta

Con los insumos locales de 3A disponibles, este procedimiento genera una réplica aislada de 3B. `--solo-verificar` contrasta imágenes, orden, formas y hashes para 3.774 IDs y comprueba los retornos y etiquetas que se usarán en entrenamiento y configuración.

```bash
python src/entrenar_3b.py "$ohlc_iteracion2" --solo-verificar

replica="$(mktemp -d)"
python src/entrenar_3b.py "$ohlc_iteracion2" --destino "$replica/corrida"
python src/seleccionar_3b.py "$ohlc_iteracion2" \
  --destino "$replica/corrida" --publico "$replica/resumen" \
  --congelado "$replica/congelado_3b.json"
python src/seleccionar_3b.py "$ohlc_iteracion2" --verificar \
  --destino "$replica/corrida" --publico "$replica/resumen" \
  --congelado "$replica/congelado_3b.json"
python src/graficar_3b.py --publico "$replica/resumen"
```

Cada CNN usa la semilla 42, Adam, lotes de 32 y ocho épocas. Genera una permutación PCG64 de los 2.210 IDs en cada época, en la misma secuencia para ambas redes. Los ocho SHA-256 de las permutaciones se guardan en el historial. Elige entre 1, 2, 4 y 8 por log loss medio por fecha en configuración y desempata por época temprana. Tras guardar y verificar los dos checkpoints, el selector genera las probabilidades del bloque de umbral y aplica la regla económica. Los pesos publicados por huella corresponden a la corrida original. Una réplica tiene su propio registro de hashes; el hardware y las versiones pueden afectar la aritmética numérica y la codificación de archivos. [Plan previo al entrenamiento](../config/entrenamiento_cnn.json) · [Protocolo](protocolo.md)

## Archivos locales y carga para la retrospectiva

Rutas relativas a la raíz de `iteracion_2`:

| Archivo | Contenido |
|---|---|
| `data/imagenes/indice.csv` y `data/imagenes/cache/` | Índice y PNG de 3A |
| `data/etapa_3b/pesos/mensual.weights.h5` | Pesos mensuales de la época 2 |
| `data/etapa_3b/pesos/mensual_diaria.weights.h5` | Pesos de dos vistas de la época 1 |
| `data/etapa_3b/probabilidades_<modelo>_<bloque>.csv` | Seis archivos por ID en entrenamiento, configuración y umbral |
| `data/etapa_3b/checkpoints.json` | Registro del ajuste antes de calcular probabilidades de umbral |
| `data/etapa_3b/etiquetas_entrenamiento_configuracion.csv`, `etiquetas_umbral.csv` y `descartes.csv` | Retornos y etiquetas operables y 510 IDs descartados, con motivo |
| [`config/congelado_3b.json`](../config/congelado_3b.json) | Umbrales, rutas y SHA-256 de los insumos, código, pesos, probabilidades y tablas |
| [`verificacion/manifiesto.csv`](../verificacion/manifiesto.csv) | IDs, fechas, elegibilidad y motivos. Incluye los 136 IDs retrospectivos y la cobertura por fecha |

SHA-256 de los pesos mensuales: `6045ea842bec8149fcf18b0ae919aeb09c87945d3cd25f582ec179cd90df6e57`.

SHA-256 de los pesos mensuales + diarios: `275709cd08920d5b2c5d0df0d20971f35888bc2f0c3a348d7e27684a963438b8`.

Este comando verifica la huella y carga cada arquitectura con sus pesos originales. La primera entrada se llama `mensual` y, en el modelo doble, la segunda se llama `diaria`. Ambas son RGB `uint8` de 192 × 192 × 3. El escalado ocurre dentro de Keras. El fragmento carga las redes y muestra el umbral; la evaluación de 2026 corresponde al bloque siguiente.

```bash
PYTHONPATH=src python - <<'PY'
from datos_3b import leer_json
from seleccionar_3b import CONGELADO, recargar_congelado

congelado = leer_json(CONGELADO)
for nombre, regla in congelado["modelos"].items():
    modelo = recargar_congelado(nombre, congelado)
    print(modelo.name, modelo.input_shape, regla["umbral"])
PY
```

Los cuatro cortes reservados son 14/07, 13/08, 14/09 y 13/10 de 2026. Los resultados de esta etapa se limitan a 2015–2025. El simulador de cartera versionado espera retornos netos por ID y una serie de probabilidades con los mismos IDs en orden. La etapa 3B calcula etiquetas e infiere exclusivamente para sus bloques autorizados. [Evaluador](../src/cartera.py) · [Alcance de 2026](protocolo.md#qué-se-había-visto)
