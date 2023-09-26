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

    @property
    def registered_webendpoints(self):
        return self.web_endpoints

    @property
    def registered_classes(self):
        pass

    @property
    def registered_entry_points(self):
        pass

    @property
    def registered_functions(self):
        pass

    def function(self):
        stub = self

        class wrapper:
            def __init__(self, func):
                
                if isinstance(func, WebEndpoint):
                    self.remote_func = ray.remote(func.handler)
                    stub.web_endpoints.append(self.remote_func)
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
    
