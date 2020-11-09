release: ./manage.py migrate
web: gunicorn --bind 0.0.0.0:$PORT optimal_transport_morphometry.wsgi
worker: REMAP_SIGTERM=SIGQUIT celery --app optimal_transport_morphometry.celery worker --loglevel INFO --without-heartbeat
