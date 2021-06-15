FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

# Install system librarires for Python and R
RUN apt clean && apt-get update && \
    apt-get install --no-install-recommends --yes \
    build-essential \
    ca-certificates \
    dpkg-dev \
    git \
    gcc \
    libbluetooth-dev \
    libbz2-dev \
    libc6-dev \
    libcurl4-gnutls-dev \
    libexpat1-dev \
    libffi-dev \
    libgdbm-dev \
    liblzma-dev \
    libncursesw5-dev \
    libpq-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl-dev \
    libxml2-dev \
    make \
    netbase \
    tk-dev \
    uuid-dev \
    wget \
    xz-utils \
    zlib1g-dev \
    python3 python3-pip python3-setuptools python3-dev \
    littler \
    r-base \
    r-base-dev \
    r-recommended \
    texlive-latex-base texlive-latex-extra \
    libpng-dev \
    parallel \
    xorg libx11-dev libgl1-mesa-dev libglu1-mesa-dev freeglut3-dev && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Only copy the setup.py, it will still force all install_requires to be installed,
# but find_packages() will find nothing (which is fine). When Docker Compose mounts the real source
# over top of this directory, the .egg-link in site-packages resolves to the mounted directory
# and all package modules are importable.
COPY ./setup.py /opt/django-project/setup.py
RUN pip install --editable /opt/django-project[dev]

# Use a directory name which will never be an import name, as isort considers this as first-party.
WORKDIR /opt/django-project
