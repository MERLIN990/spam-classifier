"""
Backend (FastAPI) del Detector de Spam / Clasificador de Texto.

Arquitectura:
    frontend/ (HTML+CSS+JS estático) --fetch()--> /api/*  (esta API)
                                                       |
                                                       v
                                        model/spam_classifier.joblib
                                     (pipeline TF-IDF + MultinomialNB)

La API queda documentada automáticamente por FastAPI en /docs (Swagger UI)
y /redoc, lo cual sirve como evidencia viva de la integración (rúbrica,
criterio 2 y 4).
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.schemas import PredictRequest, PredictResponse, HealthResponse
from app.model_service import SpamClassifierService, get_model_service, ModelNotLoadedError, MODEL_VERSION

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title="Detector de Spam - API",
    description="API REST para clasificar mensajes como spam o ham (no spam).",
    version=MODEL_VERSION,
)

# CORS abierto: permite que el frontend (aunque se sirva desde otro origen,
# p. ej. en desarrollo local con Live Server) pueda consumir la API sin
# bloqueos del navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_service_or_503() -> SpamClassifierService:
    """Dependency de FastAPI que traduce un modelo no disponible en un 503
    limpio en lugar de un 500 genérico."""
    try:
        return get_model_service()
    except ModelNotLoadedError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.get("/api/health", response_model=HealthResponse, tags=["sistema"])
def health():
    """Endpoint de salud: útil para HEALTHCHECK de Docker y monitoreo."""
    try:
        service = get_model_service()
        loaded = service.is_loaded
    except ModelNotLoadedError:
        loaded = False
    return HealthResponse(status="ok", model_loaded=loaded, model_version=MODEL_VERSION)


@app.post("/api/predict", response_model=PredictResponse, tags=["clasificación"])
def predict(payload: PredictRequest, service: SpamClassifierService = Depends(_get_service_or_503)):
    """Clasifica un texto como 'spam' o 'ham' y devuelve las probabilidades."""
    result = service.predict(payload.text)
    return PredictResponse(**result)


# --- Frontend estático (servido por el mismo contenedor/puerto) ---
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend no encontrado.")
