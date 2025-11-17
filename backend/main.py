# main.py
import os, sys
import logging
import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient, ASCENDING
from prometheus_fastapi_instrumentator import Instrumentator
from loki_logger_handler.loki_logger_handler import LokiLoggerHandler

app = FastAPI()

# -------------------------
# LOGGING
# -------------------------
logger = logging.getLogger("custom_logger")
logging_data = os.getenv("LOG_LEVEL", "INFO").upper()

if logging_data == "DEBUG":
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logger.level)
formatter = logging.Formatter(
    "%(levelname)s: %(asctime)s - %(name)s - %(message)s"
)
console_handler.setFormatter(formatter)

loki_handler = LokiLoggerHandler(
    url="http://loki:3100/loki/api/v1/push",
    labels={"application": "FastApi"},
    label_keys={},
    timeout=10,
)

logger.addHandler(console_handler)
logger.addHandler(loki_handler)
logger.info("Logger initialized")

# -------------------------
# CORS
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# MONGO
# -------------------------
MONGO_URL = os.getenv("MONGO_URL", "mongodb://admin_user:web3@mongo:27017/?authSource=admin")
mongo_client = None
collection_historial = None

try:
    mongo_client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000)
    mongo_client.admin.command("ping")
    database = mongo_client["practica1"]
    collection_historial = database["historial"]
    print("✅ Mongo conectado")
except Exception as e:
    print("⚠️ Mongo no disponible aún:", e)

# -------------------------
# Helpers
# -------------------------

def validar_operadores(a, b):
    """Valida que los parámetros existan y sean numéricos."""
    if a is None or b is None:
        raise HTTPException(
            status_code=400,
            detail="Parámetros inválidos. Debe enviar 'a' y 'b' como números."
        )

def guardar_operacion(nombre, a, b, resultado):
    """Guarda la operación en Mongo si está disponible."""
    doc = {
        "operacion": nombre,
        "a": a,
        "b": b,
        "resultado": resultado,
        "date": datetime.datetime.now(datetime.timezone.utc)
    }

    if collection_historial is not None:
        try:
            collection_historial.insert_one(doc)
        except Exception as e:
            logger.error(f"⚠️ No se pudo guardar en Mongo: {e}")

    return doc

# -------------------------
# ENDPOINTS
# -------------------------

@app.get("/")
def health():
    return {"status": "ok", "mongo": bool(collection_historial)}

# SUMA
@app.get("/calculadora/sum")
def sumar(a: float = None, b: float = None):
    validar_operadores(a, b)

    resultado = a + b
    logger.info("Operación suma ejecutada")
    logger.debug(f"a={a}, b={b}, resultado={resultado}")

    return guardar_operacion("suma", a, b, resultado)

# RESTA
@app.get("/calculadora/resta")
def restar(a: float = None, b: float = None):
    validar_operadores(a, b)

    resultado = a - b
    logger.info("Operación resta ejecutada")
    logger.debug(f"a={a}, b={b}, resultado={resultado}")

    return guardar_operacion("resta", a, b, resultado)

# MULTIPLICACIÓN
@app.get("/calculadora/multiplicacion")
def multiplicar(a: float = None, b: float = None):
    validar_operadores(a, b)

    resultado = a * b
    logger.info("Operación multiplicación ejecutada")
    logger.debug(f"a={a}, b={b}, resultado={resultado}")

    return guardar_operacion("multiplicacion", a, b, resultado)

# DIVISIÓN
@app.get("/calculadora/division")
def division(a: float = None, b: float = None):
    validar_operadores(a, b)

    if b == 0:
        raise HTTPException(
            status_code=400,
            detail="No se puede dividir entre cero."
        )

    resultado = a / b
    logger.info("Operación división ejecutada")
    logger.debug(f"a={a}, b={b}, resultado={resultado}")

    return guardar_operacion("division", a, b, resultado)

# HISTORIAL
@app.get("/calculadora/historial")
def obtener_historial():
    docs = list(collection_historial.find({}, {"_id": 0}).sort("date", ASCENDING))

    historial = []
    for d in docs:
        dt = d.get("date")
        historial.append(
            {
                "operacion": d.get("operacion", "-"),
                "a": float(d.get("a", 0)),
                "b": float(d.get("b", 0)),
                "resultado": float(d.get("resultado", 0)),
                "date": dt.isoformat() if hasattr(dt, "isoformat") else str(dt),
            }
        )

    logger.info("Historial obtenido exitosamente")
    logger.debug(f"Historial: {historial}")

    return {"historial": historial}

# PROMETHEUS
instrumentator = Instrumentator().instrument(app).expose(app)
