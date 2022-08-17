FROM rocker/shiny:4.1.0

ENV DEBIAN_FRONTEND=noninteractive

# Install system librarires for Python and R
RUN apt clean && apt-get update && \
    apt-get install --no-install-recommends --yes \
    git gcc curl \
    libc6-dev libpq-dev libpng-dev \
    python3.9 python3.9-dev python3-setuptools \
    texlive-latex-base texlive-latex-extra \
    parallel \
    xorg libx11-dev libgl1-mesa-dev libglu1-mesa-dev freeglut3-dev && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install pip
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3.9 get-pip.py && rm get-pip.py

# For some reason this is needed
RUN pip3 install cffi

# Install
ADD . /opt/django-project
RUN pip3 install -e /opt/django-project[dev,worker]

# Clone UTM R scripts and install packages
RUN git clone https://github.com/KitwareMedical/UTM /opt/UTM
COPY ./install.R /opt/django-project/install.R
RUN Rscript /opt/django-project/install.R

# Use a directory name which will never be an import name, as isort considers this as first-party.
WORKDIR /opt/django-project


