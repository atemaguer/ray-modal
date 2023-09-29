import ray
import json
from pydantic import create_model
from starlette.requests import Request
from starlette.responses import Response

from modal.utils import HTTPMethod

def create_pydantic_model(name:str, dct: dict):
    
    fields = {k: (type(v), ...) for k, v in dct.items()}

    model = create_model(name, **fields)

    return model

async def serialize_request(request: Request):
    body = await request.body()

    return {
        "method": request.method,
        "url": str(request.url),
        "uri": str(request.url.path),
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "cookies": request.cookies,
        "client": request.client.host,
        "body": body.decode("utf-8"),
    }

def coerce_dict_ints(data):
    coerced_dict = {}

    for key, value in data.items():
        try:
            coerced_dict[key] = int(value)
        except:
            coerced_dict[key] = value

    return coerced_dict

class HTTPProxy:
    def __init__(self) -> None:
        self.handlers = {}
    
    def register_endpoint(self, endpoint, handler):
        self.handlers[endpoint] = handler

    async def __call__(self, scope, receive, send):
        
        request = Request(scope, receive)

        await self.handlers["index"](scope, receive, send)

        """
        serialized_request = await serialize_request(request)

        method = serialized_request["method"]
        query_params = serialized_request["query_params"]
        body = json.loads(serialized_request["body"]) if serialized_request["body"] else {}

        handler = self.handlers["index"]

        if method == HTTPMethod.GET:
            query_params = coerce_dict_ints(query_params)
            print(**query_params)
            result = ray.get(handler.remote(**query_params))

        elif method == HTTPMethod.POST:
            RequestBody = create_pydantic_model("Body", body)
            body = RequestBody(**body)
            result = handler.remote(body)
        else:
            pass
        """

        # response = Response(result)
    
        # await response(scope, receive, send)