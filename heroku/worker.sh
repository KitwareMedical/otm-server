#!/bin/sh

# Install extra deps
pip install .[worker]


# Normal run command
REMAP_SIGTERM=SIGQUIT celery --app optimal_transport_morphometry.celery worker --loglevel INFO --without-heartbeat
