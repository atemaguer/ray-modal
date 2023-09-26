import ray
from pydantic import create_model
from starlette.requests import Request
from starlette.responses import Response

def create_pydantic_model(name:str, dct: dict):
    
    fields = {k: (type(v), ...) for k, v in dct.items()}

    model = create_model(name, **fields)

    return model

async def serialize_request(request: Request):
    body = await request.body()

    return {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "cookies": request.cookies,
        "client": request.client.host,
        "body": body.decode("utf-8"),
    }

class HTTPProxy:
    def __init__(self) -> None:
        self.handlers = {}
    
    def register_endpoint(self, endpoint, handler):
        self.handlers[endpoint] = handler

    async def __call__(self, scope, receive, send):
        print("request recieved")
        
        request = Request(scope, receive)
        serialized_request = serialize_request(request)

        handler = self.handlers["index"]

        result = handler.remote(serialized_request)

        response = Response(result)

        await response(scope, receive, send)