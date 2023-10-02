import sys

class InvalidError(Exception):
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

class Image:
    def __init__(self) -> None:
        self.dockerfile_commands = []

    def debian_slim(self):
        python_version = _dockerhub_python_version(python_version)

        self.dockerfile_commands = [
            f"FROM python:{python_version}-slim-bullseye",
            "COPY /modal_requirements.txt /modal_requirements.txt",
            "RUN apt-get update",
            "RUN apt-get install -y gcc gfortran build-essential",
            "RUN pip install --upgrade pip",
            "RUN pip install -r /modal_requirements.txt",
            # Set debian front-end to non-interactive to avoid users getting stuck with input
            # prompts.
            "RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections",
        ]

    def pip_install(self, *args):
        pass

    def app_install(self, *args):
        pass

    def run_commands(self, *args):
        pass

    def from_registry(self, name):
        pass

    def from_dockerfile(self):
        pass