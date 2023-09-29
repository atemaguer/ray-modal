from modal import Stub, web_endpoint

stub = Stub()

@stub.function()
@web_endpoint()
def square(x: int):
    return x**2