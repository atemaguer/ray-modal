from modal.utils import WebEndpoint, HTTPMethod
from fastapi import FastAPI

def web_endpoint(method: HTTPMethod = "GET"):
    app = FastAPI() 

    def decorator(func):
        if method == HTTPMethod.GET:
            app.get("/")(func)
        elif method == HTTPMethod.POST:
            app.post("/")(func)
        else:
            app.delete("/")(func)

        def handler(*args, **kwargs):
            return app(*args, **kwargs)
        
        return WebEndpoint(path=f'{func.__name__}', handler=handler)
    
    return decorator

def asgi_app():
    pass