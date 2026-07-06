"""
Fixture compartida: garantiza que exista un modelo entrenado antes de correr
la suite de pruebas, entrenándolo automáticamente si hace falta (para que
`pytest` funcione con un solo comando, sin pasos manuales previos).
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT_DIR / "model" / "spam_classifier.joblib"


@pytest.fixture(scope="session", autouse=True)
def ensure_model_trained():
    if not MODEL_PATH.exists():
        subprocess.run(
            [sys.executable, "-m", "model.train"],
            check=True,
            cwd=str(ROOT_DIR),
        )
    yield
