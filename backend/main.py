# main.py
import os
import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson import ObjectId # Importante para manejar el _id de Mongo

# --- Helper para convertir el ObjectId de Mongo a str ---
# Esto es necesario porque el tipo ObjectId no es serializable a JSON directamente.
def mongo_id_to_str(document):
    if "_id" in document and isinstance(document["_id"], ObjectId):
        document["_id"] = str(document["_id"])
    return document

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

MONGO_URL = os.getenv("MONGO_URL", "mongodb://admin_user:web3@mongo:27017/?authSource=admin")
mongo_client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)

try:
    mongo_client.admin.command("ping")
    print("Conexión con MongoDB exitosa.")
except Exception as e:
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

# --- ¡NUEVO ENDPOINT DE HISTORIAL! ---
@app.get("/calculadora/historial")
def obtener_historial():
    """
    Recupera todas las operaciones guardadas en la base de datos,
    ordenadas de la más reciente a la más antigua.
    """
    # Usamos find() para obtener todos los documentos.
    # El sort("_id", -1) ordena los resultados por fecha de creación descendente.
    historial_cursor = collection_historial.find().sort("_id", -1)
    
    # Convertimos el cursor a una lista y nos aseguramos de que el _id sea un string
    historial_lista = [mongo_id_to_str(doc) for doc in historial_cursor]
    
    return {"historial": historial_lista}
