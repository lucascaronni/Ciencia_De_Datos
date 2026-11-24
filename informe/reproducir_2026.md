# Reproducir la evaluación retrospectiva de 2026

## Comando de reproducción

Ejecutar desde la raíz de `iteracion_2`, con el entorno e insumos del workspace. Si hace falta preparar el entorno, usar las [dependencias fijadas](../requirements-cnn.txt).

```bash
source .venv/bin/activate
export KERAS_BACKEND=jax JAX_PLATFORMS=cpu
replica="$(mktemp -d)"
python src/evaluar_2026.py --destino "$replica/resultados"
```

El destino debe ser un directorio nuevo. Sin `--destino`, el evaluador escribe en `verificacion/etapa_4`. Si el OHLC está en otra ubicación, pasar `--ohlc /ruta/al/archivo.csv`. Para reconstruir el manifiesto, verificar los PNG y reproducir el control de 3B sin inferir ni valorar 2026, ejecutar `python src/evaluar_2026.py --solo-verificar` en el mismo entorno.

La configuración y el evaluador se registraron antes de abrir los resultados de 2026, en el commit local `8102aa7`. El [commit publicado con el mismo árbol](https://github.com/lucascaronni/Ciencia_De_Datos/commit/c19ea74a4332d8db709254988e4b8827291a2666) desciende del [cierre de 3B](https://github.com/lucascaronni/Ciencia_De_Datos/commit/da093192ce0b8d30210dff6e9c4345a209b57b66). El evaluador coteja el manifiesto completo reconstruido a partir de activo y fecha con la versión congelada. Verifica los 7.820 PNG del índice por SHA-256 y los hashes ordenados de 3A. En la evaluación, ambas redes reciben el mismo tensor mensual, en el mismo orden de IDs. La segunda recibe también el tensor diario.

La verificación de 3B recargó los pesos y volvió a obtener las probabilidades por ID en entrenamiento, configuración y umbral. Las seis series dieron error absoluto máximo 0 con tolerancia fijada de `1e-6`. Se reprodujeron las decisiones de la grilla de 3B, los dos umbrales, las tablas y las métricas guardadas. El evaluador aplica 0,50 directamente a las dos redes para 2026. [Configuración de 2026](../config/evaluacion_2026.json) · [Control de la corrida](../verificacion/etapa_4/control.json) · [Reproducción de 3B](reproducir_3b.md)

## Insumos locales y huellas

Rutas relativas a la raíz del repositorio.

| Insumo | Ruta | SHA-256 |
|---|---|---|
| OHLC ajustado | `../entregables/02 — Base semanal/OHLC_diario_yf20261114T2019Z.csv` | `7906de97be2145f79434dcb1f0a474d2c01ed1da7cc4a7dad1ce63c35683eb31` |
| Índice de imágenes | `data/imagenes/indice.csv` | `5064cd62f564415de489edaa5fb831b019b56ceac599edd15581c90edfa1c211` |
| PNG | `data/imagenes/cache/{mensual,diaria}/` | Cada hash está en el índice. Los hashes de los pares ID/PNG en orden están en el [control de 3A](../verificacion/imagenes/controles.json). |
| Pesos mensuales, época 2 | `data/etapa_3b/pesos/mensual.weights.h5` | `6045ea842bec8149fcf18b0ae919aeb09c87945d3cd25f582ec179cd90df6e57` |
| Pesos de dos vistas, época 1 | `data/etapa_3b/pesos/mensual_diaria.weights.h5` | `275709cd08920d5b2c5d0df0d20971f35888bc2f0c3a348d7e27684a963438b8` |
| Registro, probabilidades y etiquetas de 3B | `data/etapa_3b/` | [Rutas](reproducir_3b.md#archivos-locales-y-carga-para-la-retrospectiva) y [huellas](../config/congelado_3b.json) |

El [registro congelado de 3B](../config/congelado_3b.json) también fija los hashes del manifiesto, el protocolo, la arquitectura, el render, sus escalas y las dependencias. El [control de esta corrida](../verificacion/etapa_4/control.json) registra los hashes del evaluador y la configuración ejecutados. Los archivos del cuadro permanecen en el workspace.
