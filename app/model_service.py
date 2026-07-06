"""
Capa de servicio del modelo: carga el pipeline entrenado (TF-IDF + Naive
Bayes) una sola vez (patrón singleton) y expone una función `predict`
sencilla para que la API no dependa directamente de los detalles de
scikit-learn.
"""
from pathlib import Path
from functools import lru_cache

import joblib

MODEL_PATH = Path(__file__).resolve().parent.parent / "model" / "spam_classifier.joblib"
MODEL_VERSION = "1.0.0"


class ModelNotLoadedError(RuntimeError):
    pass


class SpamClassifierService:
    def __init__(self, model_path: Path = MODEL_PATH):
        self.model_path = model_path
        self._pipeline = None

    def load(self):
        if not self.model_path.exists():
            raise ModelNotLoadedError(
                f"No se encontró el modelo entrenado en {self.model_path}. "
                "Ejecuta 'python -m model.train' antes de iniciar la API."
            )
        self._pipeline = joblib.load(self.model_path)
        return self

    @property
    def is_loaded(self) -> bool:
        return self._pipeline is not None

    def predict(self, text: str) -> dict:
        if self._pipeline is None:
            raise ModelNotLoadedError("El modelo no está cargado todavía.")

        # Se normaliza None -> "" para que la API nunca truene por texto
        # ausente; un texto vacío simplemente cae de vuelta a la probabilidad
        # a priori aprendida por el modelo (comportamiento validado en
        # docs/VALIDACION_PRUEBAS.md).
        safe_text = text if isinstance(text, str) else ""

        classes = list(self._pipeline.classes_)
        proba = self._pipeline.predict_proba([safe_text])[0]
        proba_map = {cls: float(p) for cls, p in zip(classes, proba)}
        label = max(proba_map, key=proba_map.get)

        return {
            "label": label,
            "spam_probability": round(proba_map.get("spam", 0.0), 6),
            "ham_probability": round(proba_map.get("ham", 0.0), 6),
            "text_length": len(safe_text),
        }


@lru_cache
def get_model_service() -> SpamClassifierService:
    """Dependency de FastAPI: crea (una sola vez) y devuelve el servicio."""
    service = SpamClassifierService()
    service.load()
    return service
