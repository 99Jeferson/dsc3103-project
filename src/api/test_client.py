import requests

BASE = "http://localhost:8000"

valid = {
    "market": "Owino",
    "commodity": "Maize",
    "date": "2026-03-15",
    "rainfall_mm": 4.2,
}


def show(title, response):
    print(f"--- {title}: HTTP {response.status_code}")
    print(response.json())


if __name__ == "__main__":
    show("health", requests.get(f"{BASE}/health", timeout=10))
    show("valid prediction", requests.post(f"{BASE}/predict", json=valid, timeout=10))
    invalid = {**valid, "rainfall_mm": -5}
    show("invalid prediction", requests.post(f"{BASE}/predict", json=invalid, timeout=10))
