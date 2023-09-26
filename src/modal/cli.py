import typer
import click
import uvicorn

from modal.utils import load_module

from modal.proxy import HTTPProxy

app = typer.Typer(help="Ray Modal client.")

def _extract_args(ctx: typer.Context):
    args = { ctx.args[i].lstrip("--") : ctx.args[i+1] for i in range(0, len(ctx.args), 2)}
    return args

@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def run(executable_path: str, ctx: typer.Context):
    args = _extract_args(ctx) if ctx.args else None
    
    filename, func_name = executable_path.split("::")
    module = load_module(filename)
     
    func_caller = getattr(module, func_name)
    # stub = func_caller.stub
    
    if args:
        func_caller(**args)
    else:
        func_caller()

def _start_proxy(handlers):
    proxy = HTTPProxy()
    proxy.register_endpoint("index", handlers[0])
    
    uvicorn.run(proxy, host="0.0.0.0", port=8000)

@app.command()
def serve(executable_path: str):
    module = load_module(executable_path)
    stub = getattr(module, "stub")

    endpoints = stub.registered_webendpoints

    _start_proxy(endpoints)


@click.command()
@click.option("--name", prompt="Your name: ")
def hello(name):
    click.echo(f"Hello {name}")

app = typer.main.get_command(app)
app.add_command(hello, "hello")
