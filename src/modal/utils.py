import os
import importlib.util
from enum import Enum

cwd = os.getcwd()

def _extract_module_name_path(filename):
    module_name, _ = filename.split(".")
    module_path = f"{cwd}/{filename}"

    return module_name, module_path

def load_module(filename):
    module_name, module_path = _extract_module_name_path(filename)

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


class WebEndpoint:
    def __init__(self, path, handler):
        self.handler = handler
        self.path = path

class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"