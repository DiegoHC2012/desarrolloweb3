import pytest
import mongomock

from pymongo import MongoClient
from fastapi import FastAPI
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)
fake_mongo_client = mongomock.MongoClient()
fake_database = fake_mongo_client.practica1
fake_collection_historial = fake_database.historial

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

def test_sumar(monkeypatch, numeroa, numerob, resultado):
    monkeypatch.setattr(main, "collection_historial", fake_collection_historial)
    
    response = client.get(f"/calculadora/sum?a={numeroa}&b={numerob}")
    assert response.status_code == 200
    assert response.json() == {"a": numeroa, "b": numerob, "resultado": resultado}
    
    assert fake_collection_historial.find_one({"resultado": resultado, "a": numeroa, "b": numerob}) is not None

def test_historial(monkeypatch):
    monkeypatch.setattr(main, "collection_historial", fake_collection_historial)

    response = client.get("/calculadora/historial")
    assert response.status_code == 200

    #Obtenemos todos los documentos que ya fueron ingresados
    expected_data = list(fake_collection_historial.find({}))

    historial = []
    for document in expected_data:
        historial.append({
            "a": document["a"],
            "b": document["b"],
            "resultado": document["resultado"],
            "date": document["date"].isoformat()
        })
    
    print(f"DEBUG: exected_data{historial}")
    print(f"DEBUG: response.json{response.json()}")

    #Comparamos las respuestas
    assert response.json() == {"historial": historial}