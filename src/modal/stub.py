import ray
import logging

logger = logging.getLogger("ray")

class Stub:
    def __init__(self, name: str = None) -> None:
        if not ray.is_initialized():
            ray.init(address="auto")

        self.app_name = "default"

        if name:
            self.app_name = name

    def function(self):

        class wrapper:
            def __init__(self, func):
                self.local = func
                self.remote_func = ray.remote(func)
                self.stub = self
                
            def local(self, *args, **kwargs):
                return self.local(*args, **kwargs)
            
            def remote(self, *args, **kwargs):
                return ray.get(self.remote_func.remote(*args, **kwargs))

        return wrapper
    
    def local_entrypoint(self):

        def decorator(func):
            def wrapper(*args, **kwargs):
                stub = self
                func(*args, **kwargs)
            return wrapper
        
        return decorator
    
