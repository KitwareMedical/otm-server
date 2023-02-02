# Optimal Transport Morphometry

## Develop with Docker (recommended quickstart)

This is the simplest configuration for developers to start with.

### Initial Setup

1. Run `docker-compose run --rm django ./manage.py migrate`
2. Run `docker-compose run --rm django ./manage.py createsuperuser`
   and follow the prompts to create your own user
3. Run `docker-compose run --rm django ./manage.py populate_db --include-images sample_data/oasis_small.csv` to seed the database and generate a sample dataset.

### Run Application

1. Run `docker-compose up`
2. Access the site, starting at <http://localhost:8000/admin/>
3. When finished, use `Ctrl+C`

### Application Maintenance

Occasionally, new package dependencies or schema changes will necessitate
maintenance. To non-destructively update your development stack at any time:

1. Run `docker-compose pull`
2. Run `docker-compose build --pull --no-cache`
3. Run `docker-compose run --rm django ./manage.py migrate`

## Develop Natively (advanced)

This configuration still uses Docker to run attached services in the background,
but allows developers to run Python code on their native system.

### Initial Setup

1. Run `docker-compose -f ./docker-compose.yml up -d`
2. Install Python 3.9
3. Install
   [`psycopg2` build prerequisites](https://www.psycopg.org/docs/install.html#build-prerequisites)
4. Create and activate a new Python virtual environment
5. Run `pip install -e .[dev]`
6. Run `source ./dev/export-env.sh`
7. Run `./manage.py migrate`
8. Run `./manage.py createsuperuser` and follow the prompts to create your own user
9. Run `./manage.py populate_db sample_data/oasis_small.csv`

### Run Application

1. Ensure `docker-compose -f ./docker-compose.yml up -d` is still active
2. Run:
   1. `source ./dev/export-env.sh`
   2. `./manage.py runserver`
3. Run in a separate terminal:
   1. `source ./dev/export-env.sh`
   2. `celery --app optimal_transport_morphometry.celery worker --loglevel INFO --without-heartbeat`
4. When finished, run `docker-compose stop`

## Remap Service Ports (optional)

Attached services may be exposed to the host system via alternative ports. Developers who work
on multiple software projects concurrently may find this helpful to avoid port conflicts.

To do so, before running any `docker-compose` commands, set any of the environment variables:

* `DOCKER_POSTGRES_PORT`
* `DOCKER_RABBITMQ_PORT`
* `DOCKER_MINIO_PORT`

The Django server must be informed about the changes:

* When running the "Develop with Docker" configuration, override the environment variables:
  * `DJANGO_MINIO_STORAGE_MEDIA_URL`, using the port from `DOCKER_MINIO_PORT`.
* When running the "Develop Natively" configuration, override the environment variables:
  * `DJANGO_DATABASE_URL`, using the port from `DOCKER_POSTGRES_PORT`
  * `DJANGO_CELERY_BROKER_URL`, using the port from `DOCKER_RABBITMQ_PORT`
  * `DJANGO_MINIO_STORAGE_ENDPOINT`, using the port from `DOCKER_MINIO_PORT`

Since most of Django's environment variables contain additional content, use the values from
the appropriate `dev/.env.docker-compose*` file as a baseline for overrides.

## Testing

### Initial Setup

tox is used to execute all tests.
tox is installed automatically with the `dev` package extra.

When running the "Develop with Docker" configuration, all tox commands must be run as
`docker-compose run --rm django tox`; extra arguments may also be appended to this form.

### Running Tests

Run `tox` to launch the full test suite.

Individual test environments may be selectively run.
This also allows additional options to be be added.
Useful sub-commands include:

* `tox -e lint`: Run only the style checks
* `tox -e type`: Run only the type checks
* `tox -e test`: Run only the pytest-driven tests

To automatically reformat all code to comply with
some (but not all) of the style checks, run `tox -e format`.

## Database seeding

Developers should run the following command to generate a dataset and relevant
image data in their dev instance:

```bash
docker-compose run --rm django ./manage.py populate_db sample_data/oasis_small.csv
```

For now, this ensures the existence of a test dataset, and generates a pending upload
batch into it.

## Authentication Setup

In order to set up authentication for your local development environment, you need to create an application which will issue a `client_id` to set in your client app. Visit http://localhost:8000/admin/oauth2_provider/application/ and create a new one.

The settings for your new application should be as follows:

* Redirect URLs: http://localhost:8080/datasets (no trailing slash)
* Client type: Public
* Authorization grant type: Authorization code
* Client Secret: empty
* Name: A descriptive name of your choosing

In the client app directory (otm-client, currently a private repository), create a new file `.env.development.local` and set `VUE_APP_OAUTH_CLIENT_ID` to the value found in your application's "Client ID" field. This value represents a new OAuth2 public client ID.
