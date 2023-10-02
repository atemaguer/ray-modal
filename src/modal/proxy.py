from os import path
import ray
import json
from pydantic import create_model
from starlette.requests import Request
from starlette.responses import Response

from modal.utils import HTTPMethod

class HTTPProxy:
    def __init__(self) -> None:
        self.handlers = {}
    
    def register_endpoints(self, app_name, endpoints):
        
        for endpoint in endpoints:
            path = f'{app_name}/{endpoint.path}'
            self.handlers[path] = endpoint.handler
            
            print(f"Registered endpoint {path}")

    async def __call__(self, scope, receive, send):
        
        request = Request(scope, receive)

        if request.method != HTTPMethod.GET and request.method != HTTPMethod.POST:
            response = Response({"message": "Unsupported HTTP method"})
            return await response
        
        path = request.url.path.strip("/")
        scope["path"] = "/"
        scope["raw_path"] = b''

        await self.handlers[path](scope, receive, send)