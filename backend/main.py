# main.py
import os
import datetime
from fastapi import FastAPI
from pymongo import MongoClient

app = FastAPI()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://admin_user:web3@mongo:27017/?authSource=admin")
mongo_client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)

# opcional: validar conexión al arrancar
try:
    mongo_client.admin.command("ping")
except Exception as e:
    # en dev, no abortes: deja que se reconecte al llegar la primera request
    print("Mongo no disponible aún:", e)

database = mongo_client["practica1"]
collection_historial = database["historial"]

@app.get("/calculadora/sum")
def sumar(a: float, b: float):
    resultado = a + b
    document = {
        "resultado": resultado,
        "a": a,
        "b": b,
        "date": datetime.datetime.now(tz=datetime.timezone.utc),
    }
    collection_historial.insert_one(document)
    return {"a": a, "b": b, "resultado": resultado}
