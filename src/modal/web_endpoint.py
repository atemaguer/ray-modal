from enum import Enum

from modal.utils import WebEndpoint

class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"

def web_endpoint(method: HttpMethod = "GET"):
    
    def decorator(func):

        def handler(*args, **kwargs):
            return func(*args, **kwargs)
        
        return WebEndpoint(handler)
    
    return decorator

def asgi_app():
    pass