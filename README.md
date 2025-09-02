# desarrolloweb3
### Repositorio para la materia de desarrollo web 3

## Clase 1

### Instrucciones

Correr los siguientes comandos:
    - `python3 -m venv venv`
    - `venv\Scripts\activate`

Despues dentro del ambiente correr:
    - `pip install fastapi uvicorn`

Despues de hacer el main.py correr:
    - `uvicorn main:app --reload`

Probar en postman:
    - url: localhost
    - port: 8000
    - endpoint: localhost:8000/calculadora/sum?a=5&b=10
    - tipo: GET

