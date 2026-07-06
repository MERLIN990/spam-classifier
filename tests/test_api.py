"""
Pruebas de integración de la API (FastAPI TestClient): validan que el
backend responde correctamente vía HTTP, incluyendo códigos de estado,
esquema de respuesta y manejo de errores.

Ejecutar con:  pytest -v tests/test_api.py
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_ok():
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True


def test_predict_obvious_spam():
    res = client.post(
        "/api/predict",
        json={"text": "Ganaste un premio de $1000, reclama ya en http://bit.ly/premio"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["label"] == "spam"
    assert 0.0 <= body["spam_probability"] <= 1.0
    assert 0.0 <= body["ham_probability"] <= 1.0
    assert abs(body["spam_probability"] + body["ham_probability"] - 1.0) < 1e-4


def test_predict_obvious_ham():
    res = client.post(
        "/api/predict",
        json={"text": "Hola, ¿nos vemos mañana en la oficina para revisar el reporte?"},
    )
    assert res.status_code == 200
    assert res.json()["label"] == "ham"


def test_predict_missing_text_field_uses_default_empty_string():
    # "text" tiene default="" en el esquema, por lo que un body vacío es
    # válido (no debe romper la API con 500).
    res = client.post("/api/predict", json={})
    assert res.status_code == 200
    assert res.json()["label"] in ("spam", "ham")


def test_predict_wrong_type_returns_422():
    res = client.post("/api/predict", json={"text": 12345})
    assert res.status_code == 422


def test_predict_empty_string_text():
    res = client.post("/api/predict", json={"text": ""})
    assert res.status_code == 200
    body = res.json()
    assert body["text_length"] == 0


def test_predict_very_long_text():
    text = "oferta increible solo hoy " * 800  # ~21,000 caracteres
    res = client.post("/api/predict", json={"text": text})
    assert res.status_code == 200


def test_predict_html_and_emojis_do_not_break_api():
    res = client.post(
        "/api/predict",
        json={"text": "<b>hola</b> 😀 nos vemos mañana 🎉 en la oficina"},
    )
    assert res.status_code == 200


def test_frontend_index_served_at_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]


def test_static_assets_served():
    res = client.get("/static/styles.css")
    assert res.status_code == 200


def test_openapi_docs_available():
    """Evidencia viva de integración: Swagger UI generado automáticamente."""
    res = client.get("/docs")
    assert res.status_code == 200
    res_schema = client.get("/openapi.json")
    assert res_schema.status_code == 200
    paths = res_schema.json()["paths"]
    assert "/api/predict" in paths
    assert "/api/health" in paths
