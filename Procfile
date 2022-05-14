release: ./manage.py migrate
web: gunicorn --bind 0.0.0.0:$PORT optimal_transport_morphometry.wsgi
worker: ./heroku/worker.sh
