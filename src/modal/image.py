import sys
import tempfile
import docker
from typing import Any, List
from dataclasses import dataclass

from ray.runtime_env import RuntimeEnv

class InvalidError(Exception):
    pass

def _build_container():
    pass

def _validate_python_version(version: str) -> None:
    components = version.split(".")
    supported_versions = {"3.11", "3.10", "3.9", "3.8", "3.7"}
    if len(components) == 2 and version in supported_versions:
        return
    elif len(components) == 3:
        raise InvalidError(
            f"major.minor.patch version specification not valid. Supported major.minor versions are {supported_versions}."
        )
    raise InvalidError(f"Unsupported version {version}. Supported versions are {supported_versions}.")

config = {
    "image_python_version": "3.10"
}

def _dockerhub_python_version(python_version=None):
    if python_version is None:
        python_version = config["image_python_version"]
    if python_version is None:
        python_version = "%d.%d" % sys.version_info[:2]

    # We use the same major/minor version, but the highest micro version
    # See https://hub.docker.com/_/python
    latest_micro_version = {
        "3.11": "0",
        "3.10": "8",
        "3.9": "15",
        "3.8": "15",
        "3.7": "15",
    }

    major_minor_version = ".".join(python_version.split(".")[:2])
    python_version = major_minor_version + "." + latest_micro_version[major_minor_version]

    return python_version

@dataclass
class Image:
    
    dockerfile_commands: List[Any]
    image_name = "default"

    @classmethod
    def debian_slim(cls):
        # python_version = _dockerhub_python_version(python_version)

        dockerfile_commands = [
            f"FROM anyscale/ray-ml:nightly-py38-gpu",
            "RUN apt-get update",
            "RUN apt-get install -y gcc gfortran build-essential",
            "RUN pip install --upgrade pip",
            # Set debian front-end to non-interactive to avoid users getting stuck with input
            # prompts.
            "RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections",
        ]

        return cls(dockerfile_commands=dockerfile_commands)

    def build(self, image_name: str = None):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = f"{temp_dir}/Dockerfile"

            dockerfile = "\n".join(self.dockerfile_commands)

            with open(file_path, "w") as file:
                file.write(dockerfile)

            client = docker.from_env()
            
            tag = image_name

            if not tag:
                tag = self.image_name

            image,  build_logs = client.images.build(path=temp_dir, tag=tag)

    def pip_install(self, *args):
        self.dockerfile_commands.extend(
            args
        )

    def app_install(self, *args):
        pass

    def run_commands(self, *args):
        pass

    def from_registry(self, name):
        pass

    def from_dockerfile(self):
        pass