"""
Entrena el clasificador de spam/ham y serializa el pipeline completo
(vectorizador TF-IDF + modelo Naive Bayes) en un único archivo .joblib.

Se ejecuta automáticamente durante `docker build` (ver Dockerfile), de modo
que la imagen siempre contiene un modelo entrenado y reproducible a partir
de model/data/spam.csv. También puede ejecutarse manualmente:

    python -m model.train

Genera:
    model/spam_classifier.joblib   -> pipeline entrenado (para la API)
    model/metrics.json             -> métricas de evaluación (para pruebas/documentación)
"""
import json
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
)
import joblib

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "spam.csv"
MODEL_PATH = BASE_DIR / "spam_classifier.joblib"
METRICS_PATH = BASE_DIR / "metrics.json"
RANDOM_STATE = 42


def load_data():
    if not DATA_PATH.exists():
        print(f"No se encontró {DATA_PATH}. Generando dataset sintético...")
        from model.generate_dataset import main as generate_main
        generate_main()
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["text", "label"])
    return df


def build_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True)),
        ("clf", MultinomialNB(alpha=1.0)),
    ])


def main():
    df = load_data()
    X = df["text"].astype(str)
    y = df["label"].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    labels = sorted(y.unique())
    positive_label = "spam" if "spam" in labels else labels[0]

    metrics = {
        "n_train": len(X_train),
        "n_test": len(X_test),
        "vocab_size": len(pipeline.named_steps["tfidf"].vocabulary_),
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, pos_label=positive_label),
        "recall": recall_score(y_test, y_pred, pos_label=positive_label),
        "f1": f1_score(y_test, y_pred, pos_label=positive_label),
        "confusion_matrix": {
            "labels": labels,
            "matrix": confusion_matrix(y_test, y_pred, labels=labels).tolist(),
        },
    }

    print("=== Métricas de evaluación (20% de prueba) ===")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print(f"\nModelo guardado en: {MODEL_PATH}")
    print(f"Métricas guardadas en: {METRICS_PATH}")

    # Salvaguarda: si el desempeño cae por debajo de un umbral mínimo,
    # se hace fallar el build para no empaquetar un modelo defectuoso.
    if metrics["accuracy"] < 0.75:
        print("ERROR: accuracy por debajo del umbral mínimo (0.75).", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
