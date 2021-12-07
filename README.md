<div align="center">

# Tuber 🥔

[![Copr build status](https://copr.fedorainfracloud.org/coprs/bitbyt3r/Tuber/package/tuber/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/bitbyt3r/Tuber/package/tuber/)
[![Heroku CI Status](https://tuber-ci-badge.herokuapp.com/last.svg)](https://dashboard.heroku.com/pipelines/6ebd065d-db02-419d-80bd-6406f271d992/tests)
[![codecov](https://codecov.io/gh/magfest/tuber/branch/master/graph/badge.svg)](https://codecov.io/gh/magfest/tuber)
[![Read the Docs](https://img.shields.io/readthedocs/magfest-tuber)](https://magfest-tuber.readthedocs.io/en/latest/)

[![ci-backend](https://github.com/magfest/tuber/actions/workflows/ci-backend.yaml/badge.svg)](https://github.com/magfest/tuber/tree/main/.github/workflows/ci-backend.yaml)
[![ci-frontend](https://github.com/magfest/tuber/actions/workflows/ci-frontend.yaml/badge.svg)](https://github.com/magfest/tuber/tree/main/.github/workflows/ci-frontend.yaml)

</div>

# Table of Contents

- [Deployment](#deployment)

  - [Using Packages](#using-packages)
  - [Using Heroku](#using-heroku)
  - [Using Docker](#using-docker)

- [Development](#development)
  - [Backend](#backend)
  - [Frontend](#frontend)
  - [Database Migrations](#database-migrations)
  - [Troubleshooting](#troubleshooting)
    - [Mac Developer Setup](#mac-developer-setup)
    - [Alembic with Multiple Heads](#alembic-with-multiple-heads)

## Deployment

Tuber needs a database, a session store, and a job store as well as a web server. For testing and development you can use a single sqlite database as the database, session store and job store while using the build-in python and node webservers for a very simple deployment. Larger systems will benefit greatly from using a dedicated database instance (generally postgres), a redis server for sessions and jobs, and nginx or apache as a webserver.

There are numerous ways to configure things, but we try to make the most common was as simple as possible to implement.

### Using Docker

The latest version of Tuber is published to GitHub Packages as `ghcr.io/magfest/tuber-frontend:latest` and `ghcr.io/magfest/tuber-backend:latest`. [You can view them here.](https://github.com/orgs/magfest/packages?repo_name=tuber)

To deploy using docker first install docker on your platform, as described [here](https://docs.docker.com/get-docker/).

With the docker daemon running, you can now pull and run tuber:

```bash
docker-compose up
```

This will set up a small production-style stack of containers, using postgres for the database, nginx as a reverse proxy, and redis as the session and job store. Once it finishes starting you should be able to access your instance at [http://localhost:8081](http://localhost:8081)

Note: The sample docker-compose file does not currently configure SSL. You should either set up a reverse proxy to handle SSL, or edit `contrib/nginx.conf` to use your certificates and edit `docker-compose.yml` to allow access to port 443.

#### Developing with Docker

Any changes made locally in the development environment can be tested in docker by building the image locally and running with `docker-compose -f docker-compose.dev.yml up --build`. This will rebuild the image each time the command is run.

### Using Packages

We provide a packaged version which will install Gunicorn and includes a basic nginx config file. All sessions and other state are stored in the database, so it is possible to scale horizontally by running multiple tuber servers in front of the same database.

This software is currently only packaged for RHEL/Fedora. Builds are available on COPR:

```bash
dnf copr enable bitbyt3r/Tuber
dnf install tuber
systemctl start tuber
systemctl enable tuber
cp /usr/share/tuber/nginx.conf /etc/nginx/conf.d/tuber.conf
systemctl start nginx
systemctl enable nginx
```

You can also run tuber directly on the command line to use the built in webserver, but this is not recommended for production deploys:

```bash
dnf copr enable bitbyt3r/Tuber
dnf install copr
tuber
```

Configuration is in environment variables with some defaults preset. The main configuration required is for a database. The default database is sqlite, so for production deploys you should probably set up mariadb/mysql/postgres or any other database supported by SQLAlchemy.

To set up the database, you will have to create a database and a user with all privileges on that database. Tuber will automatically create all necessary tables and handle future migrations at server startup. The database type, username, password, hostname, and database name all get combined as a database URI [as documented by SQLAlchemy](https://docs.sqlalchemy.org/en/13/core/engines.html).

### Using Heroku

Heroku configuration is in a combination of app.json and Procfile.

Opening a PR against magfest/tuber will automatically deploy a testing environment for your PR. Merging to master moves that code to staging.

If you would like to deploy your own instance:

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Development

After cloning this repository you will need the following dependencies:

```bash
dnf install npm python3 python3-devel python3-pip # Fedora/RHEL/CentOS
apt install npm python3 python3-dev python3-pip # Debian/Ubuntu
brew install npm python # MacOS
```

On Windows you'll have to install [nodejs](https://nodejs.org/en/download/), [Python3](https://www.python.org/downloads/) and [postgreSQL](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).
Make sure to add both npm and python to your PATH during installation.

Once the dependencies are installed you can start up the backend and frontend development servers:

### Backend

Tuber uses environment variables to configure some basic settings.

```bash
DATABASE_URL=sqlite:///database.db
FLASK_ENV=production
REDIS_URL=
WORKERS=2
CIRCUITBREAKER_THREADS=2
CIRCUITBREAKER_TIMEOUT=5
ENABLE_CIRCUITBREAKER=true
```

```bash
python -m venv venv
source venv/bin/activate
cd backend
python setup.py develop
tuber

# Windows
python -m venv venv
venv\Scripts\activate.bat
cd backend
python setup.py develop
..\venv\Scripts\tuber.exe
```

The server should now start up and begin listening on port 8080 for API requests.

### Frontend

In a separate terminal from the backend, install and serve the vue frontend:

```bash
npm install --global yarn # Yarn is recommended for the frontend

cd frontend
yarn install
yarn run serve
```

This will start the frontend on port 8081. You can connect your browser to http://localhost:8081 and complete the initial setup page to begin using tuber.

Both the frontend and backend will hot-reload as you change code.

### Database Migrations

If you want to create a new table or modify an existing one you will need to create an alembic migration. Most of the time, you can do this by autogenerating it.

First, create the table definition in `tuber/models/<name>.py`, and make sure it is imported in `tuber/models/__init__.py`.

Next, use alembic to create the migration file:

```bash
venv/bin/alembic -c backend/tuber/alembic.ini revision --autogenerate -m "Added widget column to the whatsit table"
```

This should create a migration file in migrations/versions. Read through it and adjust the steps as necessary. The next time you restart your dev instance it will run the migration.

You can also trigger the database update manually:

```bash
venv/bin/alembic -c backend/tuber/alembic.ini upgrade head
```

Make sure to commit the migration along with the code that uses it!

### Troubleshooting

#### Mac developer setup

If you receive the following ambiguous error message while running `python setup.py develop`: `ld: library not found for -lssl`

Try setting the link path for openssl and running it again: `export LDFLAGS="-L/usr/local/opt/openssl/lib"`

#### Alembic with multiple heads

Sometimes when merging a branch that has its own new migrations into your own branch you'll have to tell alembic what to do.
If you see alembic complaining about multiple heads check here: https://blog.jerrycodes.com/multiple-heads-in-alembic-migrations/
