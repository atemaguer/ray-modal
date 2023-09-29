import ray
import logging
import inspect


from modal.utils import WebEndpoint

logger = logging.getLogger("ray")

class Stub:
    def __init__(self, name: str = None) -> None:
        if not ray.is_initialized():
            ray.init(address="auto")

        self.app_name = "default"

        if name:
            self.app_name = name

        self.web_endpoints = []
        self.classes = []
        self.functions = []
        self.entry_points = []

    @property
    def registered_webendpoints(self):
        return self.web_endpoints

    @property
    def registered_classes(self):
        return self.classes

    @property
    def registered_entry_points(self):
        return self.entry_points

    @property
    def registered_functions(self):
        return self.functions

    def function(self):
        stub = self

        class wrapper:
            def __init__(self, func):
                
                if isinstance(func, WebEndpoint):
                    #self.remote_func = ray.remote(func.handler)
                    stub.web_endpoints.append(func.handler)
                else:
                    self.remote_func = ray.remote(func)
                    stub.functions.append(self.remote_func)
                    self.local_func = func

                self.stub = stub

            def __call__(self, *args, **kwargs):
                return self.local_func(*args, **kwargs)
            
            def local(self, *args, **kwargs):
                return self.local_func(*args, **kwargs)
            
            def remote(self, *args, **kwargs):
                return ray.get(self.remote_func.remote(*args, **kwargs))

        return wrapper
    
    def cls(self):
        pass

    def local_entrypoint(self):

        def decorator(func):
            def wrapper(*args, **kwargs):
                stub = self
                func(*args, **kwargs)
            return wrapper
        
        return decorator
    
