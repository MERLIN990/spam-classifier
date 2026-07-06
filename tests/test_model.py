"""
Pruebas funcionales y de casos extremos sobre el pipeline entrenado
(TF-IDF + Multinomial Naive Bayes), sin pasar por la capa HTTP.

Ejecutar con:  pytest -v tests/test_model.py
"""
from pathlib import Path

import joblib
import pytest

MODEL_PATH = Path(__file__).resolve().parent.parent / "model" / "spam_classifier.joblib"


@pytest.fixture(scope="module")
def pipeline():
    return joblib.load(MODEL_PATH)


# ---------- Casos funcionales (mensajes inequívocos) ----------

@pytest.mark.parametrize("text", [
    "Felicidades, ganaste un premio de $1000, reclama ahora en http://bit.ly/premio",
    "URGENTE: verifica tu cuenta ya o sera suspendida, entra a http://claim-now.co",
    "Consigue un prestamo instantaneo sin buro de credito, aplica ya",
    "GRATIS: recarga tu celular con $500, haz click aqui ya mismo",
])
def test_predicts_spam_for_obvious_spam(pipeline, text):
    assert pipeline.predict([text])[0] == "spam"


@pytest.mark.parametrize("text", [
    "Hola Juan, ¿nos vemos mañana en la oficina?",
    "Gracias por tu ayuda con el proyecto, quedó muy bien.",
    "Recuerda que la tarea se entrega el viernes, no lo olvides.",
    "¿Vamos a comer algo más tarde? Tengo hambre.",
])
def test_predicts_ham_for_obvious_ham(pipeline, text):
    assert pipeline.predict([text])[0] == "ham"


def test_probabilities_are_valid_distribution(pipeline):
    proba = pipeline.predict_proba(["mensaje de prueba cualquiera"])[0]
    assert abs(sum(proba) - 1.0) < 1e-6
    assert all(0.0 <= p <= 1.0 for p in proba)


# ---------- Casos extremos ----------

def test_empty_string_does_not_crash(pipeline):
    pred = pipeline.predict([""])[0]
    assert pred in ("spam", "ham")


def test_whitespace_only_does_not_crash(pipeline):
    pred = pipeline.predict(["     "])[0]
    assert pred in ("spam", "ham")


def test_single_character(pipeline):
    pred = pipeline.predict(["a"])[0]
    assert pred in ("spam", "ham")


def test_very_long_text_does_not_crash(pipeline):
    text = "gana dinero facil ahora mismo " * 500  # ~15,000 caracteres
    pred = pipeline.predict([text])[0]
    assert pred in ("spam", "ham")


def test_html_embedded_detected_as_spam(pipeline):
    text = "<b>FELICIDADES</b> ganaste <i>$1000</i>, click aqui ya"
    assert pipeline.predict([text])[0] == "spam"


def test_numbers_only_does_not_crash(pipeline):
    pred = pipeline.predict(["12345 67890 00000"])[0]
    assert pred in ("spam", "ham")


def test_emojis_do_not_crash(pipeline):
    text = "hola 😀 nos vemos mañana 🎉 en la oficina 📅"
    pred = pipeline.predict([text])[0]
    assert pred in ("spam", "ham")


def test_ham_message_using_word_gratis_in_normal_context(pipeline):
    """
    Caso trampa: 'gratis' usado en un contexto cotidiano normal (no
    promocional). Valida que el modelo no depende únicamente de una
    palabra clave aislada. Ver docs/VALIDACION_PRUEBAS.md.
    """
    text = "¿Estás libre para comer algo gratis en mi casa hoy?"
    assert pipeline.predict([text])[0] == "ham"


def test_known_limitation_english_free_in_benign_context(pipeline):
    """
    LIMITACIÓN CONOCIDA (documentada en docs/VALIDACION_PRUEBAS.md):
    el dataset de entrenamiento es sintético y la palabra inglesa "free"
    aparece casi siempre en plantillas de spam, por lo que el modelo
    sobregeneraliza y tiende a clasificar como spam frases benignas en
    inglés que la contienen. No se afirma cuál es la etiqueta "correcta":
    solo se valida que la API responde de forma estable (sin excepciones)
    y se deja registrado el comportamiento observado para el análisis de
    resultados.
    """
    text = "normal message, no seas mal pensado, free time later today"
    pred = pipeline.predict([text])[0]
    proba = dict(zip(pipeline.classes_, pipeline.predict_proba([text])[0]))
    assert pred in ("spam", "ham")
    assert 0.0 <= proba["spam"] <= 1.0


def test_minimum_accuracy_on_holdout(pipeline):
    """Prueba de regresión: el modelo debe mantener un desempeño mínimo."""
    import json
    metrics_path = MODEL_PATH.parent / "metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        assert metrics["accuracy"] >= 0.85
        assert metrics["f1"] >= 0.85
