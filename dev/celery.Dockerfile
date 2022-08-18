FROM rocker/shiny:4.1.0

ENV DEBIAN_FRONTEND=noninteractive

# Install system librarires for Python and R
RUN apt clean && apt-get update && \
    apt-get install --no-install-recommends --yes \
    git gcc \
    libc6-dev libpq-dev libpng-dev \
    python3 python3-pip python3-setuptools python3-dev \
    texlive-latex-base texlive-latex-extra \
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
RUN pip3 install --editable /opt/django-project[dev]
RUN pip3 install django-s3-file-field[minio]

# Clone UTM R scripts and install packages
RUN git clone https://github.com/KitwareMedical/UTM /opt/UTM
COPY ./install.R /opt/django-project/install.R
RUN Rscript /opt/django-project/install.R

# Use a directory name which will never be an import name, as isort considers this as first-party.
WORKDIR /opt/django-project
