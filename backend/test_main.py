# test_main.py

import pytest
import mongomock
from fastapi.testclient import TestClient
import main
import datetime

client = TestClient(main.app)

@pytest.fixture
def clean_db_session(monkeypatch):
    """
    Fixture de Pytest que prepara una base de datos mock para cada prueba.
    """
    fake_mongo_client = mongomock.MongoClient()
    fake_collection = fake_mongo_client.practica1.historial
    
    main.app.state.collection_historial = fake_collection
    
    yield fake_collection
    
    fake_mongo_client.close()

# --- Pruebas para Endpoints GET con N Números ---

@pytest.mark.parametrize("numeros, resultado_esperado", [
    ([10, 20, 30], 60),
    ([5.5, 4.5], 10.0),
    ([0, 0, 0], 0),
])
def test_sumar_con_n_numeros(clean_db_session, numeros, resultado_esperado):
    response = client.get("/calculadora/sum", params={"nums": numeros})
    
    assert response.status_code == 200
    data = response.json()
    assert data["numeros"] == numeros
    assert data["resultado"] == resultado_esperado
    assert clean_db_session.count_documents({}) == 1

@pytest.mark.parametrize("numeros, resultado_esperado", [
    ([100, 10, 5], 85),
    ([10.5, 0.5], 10.0),
    ([5, 10], -5),
])
def test_restar_con_n_numeros(clean_db_session, numeros, resultado_esperado):
    response = client.get("/calculadora/res", params={"nums": numeros})

    assert response.status_code == 200
    data = response.json()
    assert data["numeros"] == numeros
    assert data["resultado"] == resultado_esperado

@pytest.mark.parametrize("numeros, resultado_esperado", [
    ([5, 5, 2], 50),
    ([10, 0.5], 5.0),
    ([10, 0], 0),
])
def test_multiplicar_con_n_numeros(clean_db_session, numeros, resultado_esperado):
    response = client.get("/calculadora/mul", params={"nums": numeros})
    
    assert response.status_code == 200
    data = response.json()
    assert data["numeros"] == numeros
    assert data["resultado"] == resultado_esperado

@pytest.mark.parametrize("numeros, resultado_esperado", [
    ([100, 5, 2], 10),
    ([0, 10], 0.0), # El 0 es correcto en ese lugar solo si es en el segundo no
])
def test_dividir_con_n_numeros(clean_db_session, numeros, resultado_esperado):
    response = client.get("/calculadora/div", params={"nums": numeros})
    
    assert response.status_code == 200
    data = response.json()
    assert data["numeros"] == numeros
    assert data["resultado"] == resultado_esperado

def test_operaciones_con_numeros_negativos(clean_db_session):
    """Prueba que todas las operaciones fallen si se envía un número negativo."""
    operaciones = ["sum", "res", "mul", "div"]
    for op in operaciones:
        response = client.get(f"/calculadora/{op}", params={"nums": [10, -5]})
        assert response.status_code == 403, f"Falló la operación {op}"
    assert clean_db_session.count_documents({}) == 0

def test_division_por_cero_en_lista(clean_db_session):
    """Prueba que la división falle si hay un cero en los divisores."""
    response = client.get("/calculadora/div", params={"nums": [100, 10, 0, 5]})
    assert response.status_code == 403
    assert clean_db_session.count_documents({}) == 0

# --- Pruebas para Lote y Historial  ---

def test_procesar_lote_exitoso(clean_db_session):
    payload = [{"op": "sum", "nums": [10, 20]}, {"op": "res", "nums": [100, 10]}]
    url = main.app.url_path_for("procesar_lote_de_operaciones")
    response = client.post(url, json=payload)
    assert response.status_code == 200
    expected = [{"op": "sum", "result": 30.0}, {"op": "res", "result": 90.0}]
    assert response.json() == expected

def test_procesar_lote_con_numeros_insuficientes(clean_db_session):
    payload = [{"op": "sum", "nums": [10, 5]}, {"op": "mul", "nums": [5]}]
    url = main.app.url_path_for("procesar_lote_de_operaciones")
    response = client.post(url, json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["message"] == "Se requieren al menos dos números para una operación."
    assert data["detail"]["operacion_fallida"] == "mul"
    assert data["detail"]["numeros_enviados"] == [5]

def test_procesar_lote_con_operacion_invalida(clean_db_session):
    payload = [{"op": "pow", "nums": [2, 3]}]
    url = main.app.url_path_for("procesar_lote_de_operaciones")
    response = client.post(url, json=payload)
    assert response.status_code == 422

def test_historial_general_con_nuevo_formato(clean_db_session):
    client.get("/calculadora/sum", params={"nums": [10, 5]})
    client.get("/calculadora/mul", params={"nums": [3, 4]})
    response = client.get("/calculadora/historial")
    assert response.status_code == 200
    data = response.json()
    assert len(data["historial"]) == 2
    resultados = {item['resultado'] for item in data['historial']}
    assert resultados == {15.0, 12.0}
    assert data['historial'][0]['numeros'] == [10, 5]

def test_historial_por_operacion_exitoso(clean_db_session):
    collection = clean_db_session
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    collection.insert_one({"operacion": "suma", "numeros": [1, 2], "resultado": 3, "date": now})
    collection.insert_one({"operacion": "suma", "numeros": [10, 10], "resultado": 20, "date": now})
    response = client.get("/calculadora/historial/operacion/suma")
    assert response.status_code == 200
    data = response.json()
    assert len(data["historial"]) == 2

def test_historial_por_fecha_exitoso(clean_db_session):
    collection = clean_db_session
    tz_utc = datetime.timezone.utc
    collection.insert_one({"operacion": "suma", "numeros": [1, 2], "resultado": 3, "date": datetime.datetime(2025, 9, 25, 10, 0, 0, tzinfo=tz_utc)})
    collection.insert_one({"operacion": "resta", "numeros": [10, 5], "resultado": 5, "date": datetime.datetime(2025, 9, 25, 15, 30, 0, tzinfo=tz_utc)})
    response = client.get("/calculadora/historial/fecha/2025-09-25")
    assert response.status_code == 200
    assert len(response.json()["historial"]) == 2

def test_historial_por_fecha_formato_invalido(clean_db_session):
    response = client.get("/calculadora/historial/fecha/25-09-2025")
    assert response.status_code == 400
    assert response.json()["detail"] == "Formato de fecha inválido. Use YYYY-MM-DD."