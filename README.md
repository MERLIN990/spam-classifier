# Detector de Spam / Clasificador de Texto

Proyecto Fase 2 — *Gestión de Proyectos de Inteligencia Artificial* (Tecmilenio).
Contenerización, integración API (frontend/backend), pruebas y despliegue en
la nube de un clasificador de texto spam/ham (TF-IDF + Naive Bayes).

## Arquitectura

```
┌─────────────────────┐        fetch('/api/predict')        ┌──────────────────────────┐
│  frontend/           │ ───────────────────────────────────▶ │  app/ (FastAPI backend)  │
│  index.html/css/js   │ ◀─────────────────────────────────── │  /api/predict            │
│  (servido por el     │           JSON {label, proba}        │  /api/health             │
│   mismo backend)     │                                       │  /docs (Swagger UI)      │
└─────────────────────┘                                       └────────────┬─────────────┘
                                                                            │ joblib.load
                                                                            ▼
                                                        model/spam_classifier.joblib
                                                        (Pipeline: TfidfVectorizer + MultinomialNB)
                                                        entrenado a partir de model/data/spam.csv
```

Un único contenedor Docker sirve tanto la API como el frontend estático,
simplificando el despliegue (un solo servicio en Render) sin sacrificar la
separación de responsabilidades entre componentes.

## Estructura del repositorio

```
spam-classifier/
├── app/                    # Backend FastAPI
│   ├── main.py             # Endpoints (/api/predict, /api/health) y montaje del frontend
│   ├── model_service.py    # Carga del modelo y lógica de predicción
│   └── schemas.py          # Esquemas Pydantic (request/response)
├── model/
│   ├── data/spam.csv       # Dataset (ver docs/VALIDACION_PRUEBAS.md, sección 3)
│   ├── generate_dataset.py # Generación reproducible del dataset
│   └── train.py            # Entrenamiento + evaluación + serialización del modelo
├── frontend/                # HTML/CSS/JS estático (sin frameworks)
├── tests/                   # pytest: modelo (test_model.py) y API (test_api.py)
├── docs/
│   ├── MANUAL_DESPLIEGUE.md    # Despliegue en Render, paso a paso
│   └── VALIDACION_PRUEBAS.md   # Metodología, resultados y casos extremos
├── Dockerfile
├── docker-compose.yml
├── render.yaml               # Blueprint opcional para despliegue por IaC
├── requirements.txt / requirements-dev.txt
└── pytest.ini
```

## Inicio rápido

### Con Docker (recomendado)

```bash
docker build -t spam-detector:local .
docker run --rm -p 8000:8000 spam-detector:local
```

o con Docker Compose:

```bash
docker compose up --build
```

Abre `http://localhost:8000` (frontend) o `http://localhost:8000/docs`
(Swagger UI de la API).

### Sin Docker (entorno virtual local)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m model.train        # entrena y serializa el modelo
uvicorn app.main:app --reload --port 8000
```

## API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/health` | Estado del servicio y si el modelo está cargado |
| POST | `/api/predict` | Clasifica un texto como `spam` o `ham` |
| GET | `/docs` | Documentación interactiva (Swagger UI) |
| GET | `/` | Frontend (interfaz web) |

Ejemplo:

```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Felicidades, ganaste un premio, reclama en http://bit.ly/premio"}'
```

```json
{
  "label": "spam",
  "spam_probability": 0.998,
  "ham_probability": 0.002,
  "text_length": 60
}
```

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest -v
```

Cubre casos funcionales (spam/ham inequívocos) y extremos (texto vacío,
muy largo, HTML, emojis, solo números, sesgos conocidos del dataset). Ver
el detalle y los resultados en [`docs/VALIDACION_PRUEBAS.md`](docs/VALIDACION_PRUEBAS.md).

## Despliegue en la nube

Guía completa paso a paso (Render) en [`docs/MANUAL_DESPLIEGUE.md`](docs/MANUAL_DESPLIEGUE.md),
incluyendo requerimientos, estrategia de despliegue y alternativas (Cloud
Run, App Runner, Container Apps).

## Modelo

- **Algoritmo**: `TfidfVectorizer` + `MultinomialNB` (scikit-learn), en un único `Pipeline` serializado con `joblib`.
- **Dataset**: sintético y reproducible (1000 mensajes, 65% ham / 35% spam) — ver justificación en `docs/VALIDACION_PRUEBAS.md`.
- **Reentrenamiento**: `python -m model.train` (o automáticamente durante `docker build`).

## Licencia

MIT — ver [`LICENSE`](LICENSE).
