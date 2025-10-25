from fastapi.testclient import TestClient
import mongomock
import pytest
import main  # <- necesitamos el módulo para patchar atributos
from main import app

client = TestClient(app)

# BD/colección falsa con mongomock
mongo_client = mongomock.MongoClient()
database = mongo_client["practica1"]
fake_collection_historial = database.historial


@pytest.mark.parametrize(
    "numeroA, numeroB, resultado",
    [
        (5, 10, 15),
        (0, 0, 0),
        (-5, 5, 0),
        (-10, -5, -15),
        (10, -20, -10),
    ],
)
def test_sumar(monkeypatch, numeroA, numeroB, resultado):
    # Redirigimos la colección usada por la app a nuestra colección fake
    monkeypatch.setattr(main, "collection_historial", fake_collection_historial, raising=False)

    response = client.get(f"/calculadora/sum?a={numeroA}&b={numeroB}")
    assert response.status_code == 200
    data = response.json()
    assert data == {"a": float(numeroA), "b": float(numeroB), "resultado": float(resultado)}


def test_historial(monkeypatch):
    # Usamos la misma colección fake para que el endpoint lea de aquí
    monkeypatch.setattr(main, "collection_historial", fake_collection_historial, raising=False)

    # Obtenemos el historial desde el endpoint
    response = client.get("/calculadora/historial")
    assert response.status_code == 200

    # Construimos el esperado a partir de lo que haya en la colección fake
    expected_data = list(fake_collection_historial.find({}))

    historial = []
    for document in expected_data:
        # Solo mapeamos los campos que expone el API
        historial.append(
            {
                "a": document["a"],
                "b": document["b"],
                "resultado": document["resultado"],
                "date": document["date"].isoformat(),
            }
        )

    print(f"Debug: expected_data: {historial}")
    print(f"Debug: response.json(): {response.json()}")

    assert response.json() == {"historial": historial}
