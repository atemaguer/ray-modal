FROM anyscale/ray-ml:nightly-py38-gpu
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get install -y gcc gfortran build-essential
RUN pip install --upgrade pip
# Set debian front-end to non-interactive to avoid users getting stuck with input
# prompts.
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections