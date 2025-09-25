from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
import mongomock
from pymongo import MongoClient

import main

client = TestClient(main.app)
fake_mongo_client = mongomock.MongoClient()
database = fake_mongo_client.practica1
collection_historial = database.historial

@pytest.mark.parametrize(
    "a, b, resultado",
    [
        (2, 3, 5),
        (4, 2, 6),
        (0, 0, 0),
        (0, 1, 1),
        (1, 0, 1),
        (1, 1, 2),
        (2, 2, 4),
    ]
)

def test_sumar(monkeypatch,a, b, resultado):
    monkeypatch.setattr(main, "collection_historial", fake_mongo_client)
    response = client.get("/calculadora/sum?a={a}&b={b}")
    assert response.status_code == 200
    assert response.json() == {"a": a, "b": b, "resultado": resultado}
    assert collection_historial.find_one({"resultado": resultado,"a": a, "b": b})

def test_historial(monkeypatch):
    monkeypatch.setattr(main, "collection_historial", collection_historial)

    response = client.get("/calculadora/historial")
    assert response.status_code == 200
    expected_data = list(collection_historial.find({}, {"_id": 0}))

    print(f"DEBUG: expected_data: {expected_data}")
    print(f"DEBUG: response.json(): {response.json()}")

    assert response.json() == expected_data