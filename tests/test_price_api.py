from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)

VALID_REQUEST = {
    "market": "Owino",
    "commodity": "Maize",
    "date": "2026-03-15",
    "rainfall_mm": 4.2,
}


def test_health_reports_serving_model_and_feature_compatibility():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["model_type"] == "LinearRegression"
    assert response.json()["feature_code_matches"] is True
    assert response.json()["model_version"]


def test_predict_returns_price_and_model_version():
    response = client.post("/predict", json=VALID_REQUEST)

    assert response.status_code == 200
    assert response.json() == {"predicted_price": 500.0, "model_version": client.get("/health").json()["model_version"]}


def test_predict_rejects_invalid_market_commodity_date_and_rainfall():
    invalid_requests = (
        {**VALID_REQUEST, "market": "Narnia"},
        {**VALID_REQUEST, "commodity": "Potatoes"},
        {**VALID_REQUEST, "date": "not-a-date"},
        {**VALID_REQUEST, "rainfall_mm": -5},
        {**VALID_REQUEST, "rainfall_mm": 501},
    )

    for request in invalid_requests:
        assert client.post("/predict", json=request).status_code == 422
