import uvicorn
from enum import Enum
from fastapi import FastAPI

class HttpMethod(Enum, str):
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"

app = FastAPI()

def web_endpoint(method: str = "GET"):

    def decorator(func):
        if method == HttpMethod.POST:
            app.post("/")(func)
        else:
            app.get("/")(func)
        
        return app
    
    return decorator

def asgi_app():
    pass