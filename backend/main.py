import os
import datetime
from fastapi import FastAPI, HTTPException, Request, Query # <-- Se añade Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from enum import Enum
from pydantic import BaseModel
from typing import List
from contextlib import asynccontextmanager

# --- Modelos Pydantic (sin cambios) ---
class TipoOperacion(str, Enum):
    suma = "sum"
    resta = "res"
    multiplicacion = "mul"
    division = "div"

class Operacion(BaseModel):
    op: TipoOperacion
    nums: List[float]

class Resultado(BaseModel):
    op: str
    result: float

# --- Gestor de Vida de la Aplicación (Lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando aplicación y conectando a MongoDB...")
    mongo_url = os.getenv("MONGO_URL", "mongodb://admin_user:web3@mongo:27017/?authSource=admin")
    app.state.mongo_client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
    try:
        app.state.mongo_client.admin.command("ping")
        print("Conexión con MongoDB exitosa.")
    except Exception as e:
        print(f"No se pudo conectar a MongoDB: {e}")
    
    app.state.collection_historial = app.state.mongo_client["practica1"]["historial"]
    
    yield

    print("Apagando aplicación y cerrando conexión a MongoDB...")
    app.state.mongo_client.close()

# --- Aplicación FastAPI ---
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# --- Endpoints base de la clase ---

@app.get("/calculadora/sum")
def sumar(request: Request, nums: List[float] = Query(..., min_length=2)):
    if any(n < 0 for n in nums):
        raise HTTPException(status_code=403, detail={"message": "Los números deben ser positivos."})
    
    resultado = sum(nums)
    document = {
        "operacion": "suma", "resultado": resultado, "numeros": nums,
        "date": datetime.datetime.now(tz=datetime.timezone.utc),
    }
    request.app.state.collection_historial.insert_one(document)
    return {"numeros": nums, "resultado": resultado}

@app.get("/calculadora/res")
def restar(request: Request, nums: List[float] = Query(..., min_length=2)):
    if any(n < 0 for n in nums):
        raise HTTPException(status_code=403, detail={"message": "Los números deben ser positivos."})
    
    resultado = nums[0]
    for numero in nums[1:]:
        resultado -= numero

    document = {
        "operacion": "resta", "resultado": resultado, "numeros": nums,
        "date": datetime.datetime.now(tz=datetime.timezone.utc),
    }
    request.app.state.collection_historial.insert_one(document)
    return {"numeros": nums, "resultado": resultado}

@app.get("/calculadora/mul")
def multiplicar(request: Request, nums: List[float] = Query(..., min_length=2)):
    if any(n < 0 for n in nums):
        raise HTTPException(status_code=403, detail={"message": "Los números deben ser positivos."})
    
    resultado = 1
    for numero in nums:
        resultado *= numero
        
    document = {
        "operacion": "multiplicacion", "resultado": resultado, "numeros": nums,
        "date": datetime.datetime.now(tz=datetime.timezone.utc),
    }
    request.app.state.collection_historial.insert_one(document)
    return {"numeros": nums, "resultado": resultado}

@app.get("/calculadora/div")
def dividir(request: Request, nums: List[float] = Query(..., min_length=2)):
    if any(n < 0 for n in nums):
        raise HTTPException(status_code=403, detail={"message": "Los números deben ser positivos."})
    
    # Verificamos que ningún divisor (del segundo número en adelante) sea cero
    if any(n == 0 for n in nums[1:]):
        raise HTTPException(status_code=403, detail={"message": "El divisor no puede ser 0."})

    resultado = nums[0]
    for numero in nums[1:]:
        resultado /= numero

    document = {
        "operacion": "division", "resultado": resultado, "numeros": nums,
        "date": datetime.datetime.now(tz=datetime.timezone.utc),
    }
    request.app.state.collection_historial.insert_one(document)
    return {"numeros": nums, "resultado": resultado}

@app.post("/calculadora/lote", response_model=List[Resultado])
def procesar_lote_de_operaciones(operaciones: List[Operacion]):
    resultados_finales = []
    for op_item in operaciones:

        if len(op_item.nums) < 2:
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "Se requieren al menos dos números para una operación.",
                    "operacion_fallida": op_item.op,
                    "numeros_enviados": op_item.nums
                }
            )

        if any(num < 0 for num in op_item.nums):
            raise HTTPException(
                status_code=403, 
                detail={
                    "message": "Los números deben ser positivos.",
                    "operacion_fallida": op_item.op,
                    "numeros_enviados": op_item.nums
                }
            )
            
        resultado_calculado = 0.0
        if op_item.op == TipoOperacion.suma:
            resultado_calculado = sum(op_item.nums)
        else:
            resultado_calculado = op_item.nums[0]
            for numero in op_item.nums[1:]:
                if op_item.op == TipoOperacion.resta:
                    resultado_calculado -= numero
                elif op_item.op == TipoOperacion.multiplicacion:
                    resultado_calculado *= numero
                elif op_item.op == TipoOperacion.division:
                    if numero == 0:
                        raise HTTPException(
                            status_code=403, 
                            detail={
                                "message": "El divisor no puede ser 0.",
                                "operacion_fallida": op_item.op,
                                "numeros_enviados": op_item.nums
                            }
                        )
                    resultado_calculado /= numero
                    
        resultados_finales.append(Resultado(op=op_item.op, result=resultado_calculado))
        
    return resultados_finales

@app.get("/calculadora/historial")
def obtener_historial(request: Request):
    historial = []
    for operacion in request.app.state.collection_historial.find({}):
        historial.append({
            "numeros": operacion.get("numeros", [operacion.get("a"), operacion.get("b")]), 
            "resultado": operacion.get("resultado"),
            "operacion": operacion.get("operacion"),
            "date": operacion.get("date").isoformat()
        })
    return {"historial": historial}

@app.get("/calculadora/historial/operacion/{operacion}")
def obtener_historial_por_operacion(operacion: str, request: Request):
    operaciones_validas = [op.name for op in TipoOperacion]
    if operacion not in operaciones_validas:
        raise HTTPException(status_code=404, detail=f"Operación '{operacion}' no encontrada.")
    cursor = request.app.state.collection_historial.find({"operacion": operacion})
    historial = []
    for doc in cursor:
        historial.append({
            "numeros": doc.get("numeros", [doc.get("a"), doc.get("b")]),
            "resultado": doc.get("resultado"),
            "operacion": doc.get("operacion"),
            "date": doc.get("date").isoformat()
        })
    return {"historial": historial}

@app.get("/calculadora/historial/fecha/{fecha}")
def obtener_historial_por_fecha(fecha: str, request: Request):
    try:
        fecha_obj = datetime.datetime.fromisoformat(fecha).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD.")
    start_of_day = datetime.datetime.combine(fecha_obj, datetime.time.min, tzinfo=datetime.timezone.utc)
    end_of_day = datetime.datetime.combine(fecha_obj, datetime.time.max, tzinfo=datetime.timezone.utc)
    query = {"date": {"$gte": start_of_day, "$lte": end_of_day}}
    cursor = request.app.state.collection_historial.find(query)
    historial = []
    for doc in cursor:
        historial.append({
            "numeros": doc.get("numeros", [doc.get("a"), doc.get("b")]),
            "resultado": doc.get("resultado"),
            "operacion": doc.get("operacion"),
            "date": doc.get("date").isoformat()
        })
    return {"historial": historial}