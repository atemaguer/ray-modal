
import os
import typer
import click
from typing import List, Optional
from typing_extensions import Annotated
import importlib.util

cwd = os.getcwd()
app = typer.Typer(help="Ray Modal client.")

def _extract_args(ctx: typer.Context):

    args = { ctx.args[i].lstrip("--") : ctx.args[i+1] for i in range(0, len(ctx.args), 2)}

    return args

@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def run(executable_path: str, ctx: typer.Context):
    args = _extract_args(ctx) if ctx.args else None
    
    file_name, func_name = executable_path.split("::")
    module_name, _ = file_name.split(".")
    module_path = f"{cwd}/{file_name}"

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
     
    func_caller = getattr(module, func_name)
    stub = func_caller.stub
    
    if args:
        func_caller(**args)
    else:
        func_caller()

@app.command()
def serve():
    print("serving application")

@click.command()
@click.option("--name", prompt="Your name: ")
def hello(name):
    click.echo(f"Hello {name}")

app = typer.main.get_command(app)
app.add_command(hello, "hello")
