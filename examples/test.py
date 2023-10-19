import sys

import modal

stub = modal.Stub("example-hello-world")

@stub.function()
def f(i):
    # print(i**2)
    return i**2


@stub.local_entrypoint()
def main():
    # Call the function locally.
    print(f.local(1000))

    # Call the function remotely.
    print(f.remote(1000))
 