import tempfile
import shutil
import docker
import os

python_version = "3.10"

# commands = [
#             f"FROM python:{python_version}-slim-bullseye",
#             "RUN apt-get update",
#             "RUN apt-get install -y gcc gfortran build-essential",
#             "RUN pip install --upgrade pip",
#             # Set debian front-end to non-interactive to avoid users getting stuck with input
#             # prompts.
#             "RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections",
#         ]

dockerfile_commands = [
            f"FROM anyscale/ray-ml:nightly-py38-gpu",
            "ENV DEBIAN_FRONTEND=noninteractive",
            "RUN apt-get install -y gcc gfortran build-essential",
            "RUN pip install --upgrade pip",
            # Set debian front-end to non-interactive to avoid users getting stuck with input
            # prompts.
            # "RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections",
        ]

with tempfile.TemporaryDirectory() as temp_dir:
    file_path = f"{temp_dir}/Dockerfile"

    dockerfile = "\n".join(dockerfile_commands)

    with open(file_path, "w") as file:
        file.write(dockerfile)

    client = docker.from_env()

    image,  build_logs = client.images.build(path=temp_dir, tag="docker-image")