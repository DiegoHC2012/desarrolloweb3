from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
import mongomock
from pymongo import MongoClient

from main import app

client = TestClient(app)

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

def test_sumar(a, b, resultado):
    response = client.get("/calculadora/sum?a={a}&b={b}")
    assert response.status_code == 200
    assert response.json() == {"a": a, "b": b, "resultado": resultado}