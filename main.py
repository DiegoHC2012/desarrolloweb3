from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/calculadora/sum")
def sumar(a: float, b: float):
    return {"a": a, "b": b, "result": a + b}
