# main.py
import os, sys
import logging
import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient, ASCENDING
from prometheus_fastapi_instrumentator import Instrumentator
from loki_logger_handler.loki_logger_handler import LokiLoggerHandler
from prometheus_client import Counter, Histogram

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
    allow_origins=["*"],
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
    logger.info("Mongo conectado")
except Exception as e:
    logger.error(f"⚠️ Mongo no disponible: {e}")

# -------------------------
# MÉTRICAS PROMETHEUS
# -------------------------

OPERACIONES_TOTAL = Counter(
    "calculadora_operaciones_total",
    "Número total de operaciones",
    ["tipo"]
)

OPERACIONES_ERROR = Counter(
    "calculadora_operaciones_error_total",
    "Número total de operaciones fallidas",
    ["tipo"]
)

OPERACIONES_DURACION = Histogram(
    "calculadora_operaciones_duracion_ms",
    "Duración de operaciones en milisegundos",
    ["tipo"]
)

# -------------------------
# HELPERS
# -------------------------

def validar_operadores(a, b):
    if a is None or b is None:
        raise HTTPException(
            status_code=400,
            detail="Parámetros inválidos: debes enviar 'a' y 'b'"
        )

def guardar_operacion(nombre, a, b, resultado):
    doc = {
        "operacion": nombre,
        "a": a,
        "b": b,
        "resultado": resultado,
        "date": datetime.datetime.now(datetime.timezone.utc)
    }

    try:
        if collection_historial:
            collection_historial.insert_one(doc)
    except Exception as e:
        logger.error(f"[MONGO ERROR] Falló el guardado: {str(e)}")

    # limpiar retorno
    if "_id" in doc:
        del doc["_id"]

    if isinstance(doc["date"], (datetime.datetime, datetime.date)):
        doc["date"] = doc["date"].isoformat()

    return doc

# -------------------------
# ENDPOINTS
# -------------------------

@app.get("/")
def health():
    return {"status": "ok", "mongo": bool(collection_historial)}

# SUMA
@app.get("/calculadora/sum")
def sumar(a: str = None, b: str = None):
    tipo = "suma"
    try:
        # Si falta un parámetro
        if a is None or b is None:
            raise HTTPException(status_code=400, detail="Faltan parámetros")

        # Intentar convertirlos a float
        try:
            a = float(a)
            b = float(b)
        except:
            raise HTTPException(status_code=400, detail="Los parámetros deben ser números")

        # Medir éxito
        OPERACIONES_TOTAL.labels(tipo).inc()
        with OPERACIONES_DURACION.labels(tipo).time():
            resultado = a + b
            logger.info(f"[SUCCESS] SUMA: a={a}, b={b}, res={resultado}")
            return guardar_operacion(tipo, a, b, resultado)

    except HTTPException as e:
        logger.error(f"[ERROR SUMA] {e.detail}")
        OPERACIONES_ERROR.labels(tipo).inc()
        raise e

    except Exception as e:
        logger.error(f"[ERROR SUMA] inesperado: {str(e)}")
        OPERACIONES_ERROR.labels(tipo).inc()
        raise HTTPException(status_code=500, detail="Error interno en SUMA")

# RESTA
@app.get("/calculadora/resta")
def restar(a: str = None, b: str = None):
    tipo = "resta"
    try:
        # Validar que existan parámetros
        if a is None or b is None:
            raise HTTPException(status_code=400, detail="Faltan parámetros")

        # Intentar parsear a número
        try:
            a = float(a)
            b = float(b)
        except:
            raise HTTPException(status_code=400, detail="Los parámetros deben ser números")

        # Contamos operación y duración
        OPERACIONES_TOTAL.labels(tipo).inc()
        with OPERACIONES_DURACION.labels(tipo).time():
            resultado = a - b
            logger.info(f"[SUCCESS] RESTA: a={a}, b={b}, res={resultado}")
            return guardar_operacion(tipo, a, b, resultado)

    except HTTPException as e:
        OPERACIONES_ERROR.labels(tipo).inc()
        logger.error(f"[ERROR RESTA] {e.detail}")
        raise e

    except Exception as e:
        OPERACIONES_ERROR.labels(tipo).inc()
        logger.error(f"[ERROR RESTA] inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno en RESTA")

# MULTIPLICACIÓN
@app.get("/calculadora/multiplicacion")
def multiplicar(a: str = None, b: str = None):
    tipo = "multiplicacion"
    try:
        # Validar que existan parámetros
        if a is None or b is None:
            raise HTTPException(status_code=400, detail="Faltan parámetros")

        # Intentar parsear a número
        try:
            a = float(a)
            b = float(b)
        except:
            raise HTTPException(status_code=400, detail="Los parámetros deben ser números")

        # Registrar operación
        OPERACIONES_TOTAL.labels(tipo).inc()
        with OPERACIONES_DURACION.labels(tipo).time():
            resultado = a * b
            logger.info(f"[SUCCESS] MULTIPLICACIÓN: a={a}, b={b}, res={resultado}")
            return guardar_operacion(tipo, a, b, resultado)

    except HTTPException as e:
        OPERACIONES_ERROR.labels(tipo).inc()
        logger.error(f"[ERROR MULTIPLICACION] {e.detail}")
        raise e

    except Exception as e:
        OPERACIONES_ERROR.labels(tipo).inc()
        logger.error(f"[ERROR MULTIPLICACION] inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno en MULTIPLICACION")

# DIVISIÓN
@app.get("/calculadora/division")
def division(a: str = None, b: str = None):
    tipo = "division"
    try:
        # Validación de parámetros
        if a is None or b is None:
            raise HTTPException(status_code=400, detail="Faltan parámetros")

        # Convertir a número
        try:
            a = float(a)
            b = float(b)
        except:
            raise HTTPException(status_code=400, detail="Los parámetros deben ser números")

        # Validación especial: división entre cero
        if b == 0:
            raise HTTPException(status_code=400, detail="No se puede dividir entre cero")

        # Registrar métricas
        OPERACIONES_TOTAL.labels(tipo).inc()
        with OPERACIONES_DURACION.labels(tipo).time():
            resultado = a / b
            logger.info(f"[SUCCESS] DIVISIÓN: a={a}, b={b}, res={resultado}")
            return guardar_operacion(tipo, a, b, resultado)

    except HTTPException as e:
        OPERACIONES_ERROR.labels(tipo).inc()
        logger.error(f"[ERROR DIVISION] {e.detail}")
        raise e

    except Exception as e:
        OPERACIONES_ERROR.labels(tipo).inc()
        logger.error(f"[ERROR DIVISION] inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno en DIVISION")

# HISTORIAL
@app.get("/calculadora/historial")
def obtener_historial():
    try:
        docs = list(collection_historial.find({}, {"_id": 0}).sort("date", ASCENDING))
        logger.info("[SUCCESS] HISTORIAL recuperado")
        return {"historial": docs}

    except Exception as e:
        logger.error(f"[ERROR HISTORIAL] {str(e)}")
        raise HTTPException(status_code=500, detail="Error obteniendo historial")

# PROMETHEUS
instrumentator = Instrumentator().instrument(app).expose(app)
