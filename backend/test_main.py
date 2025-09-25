import pytest
import mongomock

from fastapi.testclient import TestClient
# Asegúrate de que tu archivo principal se llame 'main.py' y contenga 'app'
import main 

# El cliente de prueba se inicializa una vez
client = TestClient(main.app)


@pytest.fixture
def clean_db_session(monkeypatch):
    """
    Fixture de Pytest para crear una sesión de base de datos mock y limpia para cada prueba.
    - Crea una instancia nueva de mongomock.
    - Usa monkeypatch para reemplazar la colección real de la aplicación por la mock.
    - 'yield' entrega la colección a la función de prueba.
    - Después de que la prueba termina, el contexto se limpia.
    """
    # 1. Setup: Crear una colección mock limpia antes de cada prueba
    fake_mongo_client = mongomock.MongoClient()
    fake_collection = fake_mongo_client.practica1.historial
    
    # 2. Inyectar la colección mock en el módulo 'main' de la aplicación
    monkeypatch.setattr(main, "collection_historial", fake_collection)
    
    # 3. Entregar la colección a la prueba que la use
    yield fake_collection
    
    # 4. Teardown (limpieza): se ejecuta después de la prueba
    fake_mongo_client.close()


@pytest.mark.parametrize(
    "numeroa, numerob, resultado",
    [
        (5, 10, 15),
        (0, 0, 0),
        (-5, 5, 0),
        (-10, -5, -15),
        (2.5, 2.5, 5.0),
        (10, -20, -10)
    ]
)
def test_sumar(clean_db_session, numeroa, numerob, resultado):
    response = client.get(f"/calculadora/sum?a={numeroa}&b={numerob}")
    assert response.status_code == 200
    assert response.json() == {"a": numeroa, "b": numerob, "resultado": resultado}
    
    # Verificar que el registro se guardó en la base de datos limpia
    assert clean_db_session.count_documents({}) == 1
    assert clean_db_session.find_one({"operacion": "suma", "resultado": resultado}) is not None


@pytest.mark.parametrize(
    "numeroa, numerob, resultado",
    [
        (10, 5, 5),
        (5, 10, -5),
        (0, 0, 0),
        (-5, 5, -10),
        (5.5, 2.5, 3.0),
    ]
)
def test_restar(clean_db_session, numeroa, numerob, resultado):
    response = client.get(f"/calculadora/res?a={numeroa}&b={numerob}")
    assert response.status_code == 200
    assert response.json() == {"a": numeroa, "b": numerob, "resultado": resultado}
    
    assert clean_db_session.count_documents({}) == 1
    assert clean_db_session.find_one({"operacion": "resta", "resultado": resultado}) is not None


@pytest.mark.parametrize(
    "numeroa, numerob, resultado",
    [
        (5, 10, 50),
        (5, 0, 0),
        (-5, 5, -25),
        (-10, -5, 50),
        (2.5, 2.0, 5.0),
    ]
)
def test_multiplicar(clean_db_session, numeroa, numerob, resultado):
    response = client.get(f"/calculadora/mul?a={numeroa}&b={numerob}")
    assert response.status_code == 200
    assert response.json() == {"a": numeroa, "b": numerob, "resultado": resultado}
    
    assert clean_db_session.count_documents({}) == 1
    assert clean_db_session.find_one({"operacion": "multiplicacion", "resultado": resultado}) is not None


@pytest.mark.parametrize(
    "numeroa, numerob, resultado",
    [
        (10, 5, 2.0),
        (5, 2, 2.5),
        (0, 5, 0.0),
        (-10, 5, -2.0),
    ]
)
def test_dividir(clean_db_session, numeroa, numerob, resultado):
    response = client.get(f"/calculadora/div?a={numeroa}&b={numerob}")
    assert response.status_code == 200
    assert response.json() == {"a": numeroa, "b": numerob, "resultado": resultado}

    assert clean_db_session.count_documents({}) == 1
    assert clean_db_session.find_one({"operacion": "division", "resultado": resultado}) is not None


@pytest.mark.parametrize("numeroa", [10, 0, -5, 8.5])
def test_division_cero(clean_db_session, numeroa):
    response = client.get(f"/calculadora/div?a={numeroa}&b=0")
    assert response.status_code == 400
    
    # Verificamos que no se guardó ningún registro en caso de error
    assert clean_db_session.count_documents({}) == 0


def test_historial(clean_db_session):
    # 1. Arrange: Realizamos algunas operaciones para poblar el historial
    client.get(f"/calculadora/sum?a=10&b=5")   # Resultado 15
    client.get(f"/calculadora/mul?a=3&b=4")   # Resultado 12
    client.get(f"/calculadora/res?a=10&b=20") # Resultado -10

    # 2. Act: Llamamos al endpoint del historial
    response = client.get("/calculadora/historial")
    assert response.status_code == 200
    
    data = response.json()
    historial_recibido = data.get("historial", [])

    # 3. Assert: Verificamos que el historial contiene exactamente lo que esperamos
    assert len(historial_recibido) == 3
    
    # Extraemos los resultados para verificarlos (usar un set ignora el orden)
    resultados_reales = {item["resultado"] for item in historial_recibido}
    resultados_esperados = {15.0, 12.0, -10.0}
    
    assert resultados_reales == resultados_esperados