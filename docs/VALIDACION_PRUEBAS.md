# Documento de Validación y Pruebas

Proyecto: Detector de Spam / Clasificador de Texto
Fase 2 — Gestión de Proyectos de Inteligencia Artificial

## 1. Objetivo

Validar que el modelo de clasificación (TF-IDF + Multinomial Naive Bayes) y
la API que lo expone funcionan correctamente, tanto en casos de uso
típicos como en casos extremos (*edge cases*), y dejar registro reproducible
de los resultados obtenidos.

## 2. Alcance de las pruebas

| Nivel | Herramienta | Archivo |
|---|---|---|
| Modelo (unitarias) | pytest | `tests/test_model.py` |
| API (integración, HTTP) | pytest + FastAPI TestClient | `tests/test_api.py` |
| Contenedor (end-to-end manual) | Docker + curl | Ver sección 6 |

Para ejecutar toda la suite automatizada:

```bash
pip install -r requirements-dev.txt
python -m model.train      # genera model/spam_classifier.joblib si no existe
pytest -v
```

## 3. Dataset utilizado

No se contó con acceso a internet en el entorno de desarrollo para
descargar un dataset público (p. ej. SMS Spam Collection de la UCI), por lo
que se generó un dataset sintético reproducible (`model/generate_dataset.py`,
semilla fija = 42) a partir de plantillas realistas de mensajes en español,
con sustitución aleatoria de nombres, horarios, montos, marcas y enlaces.

- Total de registros: **1000** (650 ham / 350 spam)
- División: 80% entrenamiento (800) / 20% prueba (200), estratificada
- Tamaño de vocabulario (TF-IDF sobre el set de entrenamiento): 419 términos

Se incluyeron deliberadamente mensajes "trampa" (p. ej. ham que usa la
palabra "gratis" en un contexto cotidiano) para poder evaluar si el modelo
aprende patrones reales y no solo coincidencias de palabras sueltas.

## 4. Pruebas funcionales

Ejecutando el pipeline de entrenamiento/evaluación (`python -m model.train`)
sobre el 20% de prueba (200 mensajes, held-out) se obtuvieron las siguientes
métricas:

| Métrica | Valor |
|---|---|
| Accuracy | 1.00 |
| Precision (clase *spam*) | 1.00 |
| Recall (clase *spam*) | 1.00 |
| F1-score (clase *spam*) | 1.00 |

Matriz de confusión (conjunto de prueba, 200 mensajes):

| | Predicho: ham | Predicho: spam |
|---|---|---|
| **Real: ham** | 140 (TN) | 0 (FP) |
| **Real: spam** | 0 (FN) | 60 (TP) |

Pruebas funcionales puntuales (`tests/test_model.py`, `tests/test_api.py`):

- Mensajes de spam evidentes (premios, phishing, préstamos, urgencia) → clasificados correctamente como `spam`.
- Mensajes cotidianos (saludos, planes, tareas, agradecimientos) → clasificados correctamente como `ham`.
- Las probabilidades devueltas por `/api/predict` suman 1.0 y están en el rango [0, 1].
- `GET /api/health` responde `200` con `model_loaded: true`.
- `GET /docs` y `/openapi.json` exponen la documentación interactiva de la API (Swagger UI), incluyendo `/api/predict` y `/api/health`.

## 5. Casos extremos evaluados

| # | Caso | Entrada (resumen) | Resultado observado | Análisis |
|---|---|---|---|---|
| 1 | Texto vacío | `""` | `ham`, prob. ≈ prior de clases (65/35) | Sin texto no hay señal; el modelo recae en la probabilidad a priori en lugar de fallar. La API responde `200`, no `500`. |
| 2 | Solo espacios | `"   "` | Igual que texto vacío | El tokenizador no encuentra términos; comportamiento estable. |
| 3 | Un solo carácter | `"a"` | Igual al caso base | No genera error ni predicción inestable. |
| 4 | Texto extremadamente largo | ~15,000-21,000 caracteres repetidos | Respuesta correcta y rápida | Sin *timeouts* ni errores de memoria en las pruebas realizadas. |
| 5 | Solo números | `"12345 67890 00000"` | `ham` (fuera de vocabulario) | Los números no aparecen en el vocabulario de entrenamiento; recae en el prior. |
| 6 | HTML embebido | `"<b>FELICIDADES</b> ganaste <i>$1000</i> click aqui"` | `spam` (correcto) | El tokenizador ignora las etiquetas y usa las palabras clave de spam para clasificar correctamente. |
| 7 | Emojis + texto normal | `"hola 😀 nos vemos mañana 🎉 en la oficina"` | `ham` (correcto) | Los emojis se ignoran (no son tokens alfanuméricos); no rompen la predicción. |
| 8 | "Gratis" en contexto normal | `"¿Estás libre para comer algo gratis en mi casa hoy?"` | `ham` (correcto) | El modelo combina el contexto completo, no solo la palabra "gratis". |
| 9 | Mezcla de idiomas, spam | `"FREE FREE FREE money now click ... 100% GRATIS PREMIO"` | `spam` (correcto) | Detecta señales de spam en inglés y español simultáneamente. |
| 10 | "Free" (inglés) en frase benigna | `"normal message, no seas mal pensado, free time later today"` | `spam` (⚠️ ver limitación) | Ver sección 7. |

## 6. Validación del contenedor (entorno local)

Pasos ejecutados para validar el contenedor Docker de forma local (ver
también `docs/MANUAL_DESPLIEGUE.md`, sección "Ejecución local"):

```bash
docker build -t spam-detector:local .
docker run --rm -p 8000:8000 --name spam-detector spam-detector:local

# En otra terminal:
curl http://localhost:8000/api/health
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Felicidades, ganaste un premio, reclama en http://bit.ly/premio"}'
```

Checklist de validación local (marcar al ejecutar en tu máquina):

- [ ] `docker build` finaliza sin errores (incluye el entrenamiento del modelo).
- [ ] `docker run` levanta el contenedor y el `HEALTHCHECK` reporta `healthy`.
- [ ] `GET /api/health` responde `200` con `model_loaded: true`.
- [ ] `POST /api/predict` responde `200` con `label`, `spam_probability`, `ham_probability`.
- [ ] El frontend carga correctamente en `http://localhost:8000/`.
- [ ] `pytest -v` pasa todas las pruebas.

> Nota: agrega aquí (`docs/screenshots/`) capturas de pantalla de `docker ps`,
> del frontend funcionando y de `/docs` (Swagger UI) como evidencia adicional.

## 7. Resultados y conclusiones

- El pipeline TF-IDF + Multinomial Naive Bayes alcanza un desempeño muy alto
  (accuracy/F1 = 1.0) sobre el conjunto de prueba. Esto se explica en gran
  parte porque el dataset es **sintético y generado por plantillas**, lo que
  produce clases muy separables (vocabularios de spam y ham poco
  solapados). En un dataset real (mensajes genuinos de usuarios) se espera
  un desempeño más modesto (aunque igualmente sólido, típicamente 92-98% de
  accuracy en benchmarks conocidos como SMS Spam Collection).
- El modelo demuestra **comportamiento estable ante entradas degeneradas**
  (vacío, espacios, un carácter, solo números): nunca lanza una excepción,
  siempre retorna una distribución de probabilidad válida.
- El modelo **no depende de una sola palabra clave**: el caso "gratis en
  contexto normal" se clasifica correctamente como ham, mostrando que
  combina múltiples señales léxicas.
- **Limitación conocida (sesgo del dataset):** la palabra inglesa "free"
  aparece casi exclusivamente en plantillas de spam durante el
  entrenamiento (no existen suficientes ejemplos ham en inglés que la usen
  en contexto benigno). Como resultado, la frase de prueba *"normal
  message, no seas mal pensado, free time later today"* se clasifica como
  `spam`, un **falso positivo**. Esto es un caso realista de sesgo de
  datos de entrenamiento, no un error de implementación: el modelo aprende
  exactamente lo que el dataset le enseña. Se documenta explícitamente en
  `tests/test_model.py` (`test_known_limitation_english_free_in_benign_context`)
  en vez de ocultarse.
- **Recomendaciones para producción:** (1) sustituir o enriquecer el
  dataset sintético con datos reales (SMS Spam Collection, correos
  reales anonimizados, o retroalimentación de usuarios reales); (2)
  monitorear falsos positivos/negativos en producción y reentrenar
  periódicamente (`model/train.py` está preparado para volver a
  ejecutarse con datos actualizados); (3) considerar un umbral de decisión
  ajustable (actualmente se usa argmax / 0.5) si se prioriza minimizar
  falsos positivos o falsos negativos según el caso de uso.
