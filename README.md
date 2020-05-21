# Tuber

[![Copr build status](https://copr.fedorainfracloud.org/coprs/bitbyt3r/Tuber/package/tuber/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/bitbyt3r/Tuber/package/tuber/)
[![Heroku CI Status](https://tuber-ci-badge.herokuapp.com/last.svg)](https://dashboard.heroku.com/pipelines/6ebd065d-db02-419d-80bd-6406f271d992/tests)

Table of Contents
=================

* [Deployment](#deployment)
  * [Using Packages](#using-packages)
  * [Using Heroku](#using-heroku)
  * [Using Docker](#using-docker)

* [Developing](#developing)
  * [Backend](#backend)
  * [Frontend](#frontend)
  * [Database Migrations](#database-migrations)
  * [Troubleshooting](#troubleshooting)
    * [Mac Developer Setup](#mac-developer-setup)
    * [Alembic with Multiple Heads](#alembic-with-multiple-heads)


## Deployment

### Using Packages

For production deploys it is recommended to use the RPM package, which will install Gunicorn and includes a basic nginx config file. All sessions and other state are stored in the database, so it is possible to scale horizontally by running multiple tuber servers in front of the same database.

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

Configuration is in `/etc/tuber/tuber.json`. The main configuration required is for a database. The default database is sqlite, so for production deploys you should probably set up mariadb/mysql/postgres or any other database supported by SQLAlchemy.

To set up the database, you will have to create a database and a user with all privileges on that database. Tuber will automatically create all necessary tables and handle future migrations at server startup. The database type, username, password, hostname, and database name all get combined as a database URI [as documented by SQLAlchemy](https://docs.sqlalchemy.org/en/13/core/engines.html). 

### Using Heroku

Heroku configuration is in a combination of app.json and Procfile.

Opening a PR against magfest/tuber will automatically deploy a testing environment for your PR. Merging to master moves that code to staging.

If you would like to deploy your own instance:

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### Using Docker

The latest version of Tuber is published to Docker Hub as `magfest/tuber:latest`. [You can view it here.](https://hub.docker.com/r/magfest/tuber)

To deploy using docker first install docker on your platform, as described [here](https://docs.docker.com/get-docker/).

With the docker daemon running, you can now pull and run tuber:

```bash
docker run -it --port 8080:8080 magfest/tuber:latest
```

This will start the container attached to the local terminal, and make it available on localhost:8080. This is useful as a test, but for production deployments you will want to set up a reverse proxy and a standalone postgres database container. The quickest way to accomplish this is with `docker-compose`.

```bash
git clone https://github.com/magfest/tuber.git
cd tuber
docker-compose up
```

Note: The sample docker-compose file does not currently configure SSL. You should either set up a reverse proxy to handle SSL, or edit `contrib/nginx.conf` to use your certificates and edit `docker-compose.yml` to allow access to port 443.

## Developing

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
Copy contrib/tuber.json.devel to tuber.json:
```bash
# Linux/MacOS
cp contrib/tuber.json.devel tuber.json
#Windows
copy contrib\tuber.json.devel tuber.json
```

```bash
python -m venv venv

# Linux/MacOS
venv/bin/activate 

# Windows 
venv\Scripts\activate.bat

cd backend
python setup.py develop

# Linux/MacOS
../venv/bin/tuber

# Windows
 ..\venv\Scripts\tuber.exe
```

The server should now start up and begin listening on port 8080.

### Frontend

In a separate terminal from the backend, install and serve the vue frontend:

```bash
cd frontend
npm install
npm serve
```

This will start the frontend on port 8081, however you should connect your browser to localhost:8080, as the backend proxies the frontend to provide a single endpoint to the browser so that the CORS environment of the development environment matches the production deployment.

### Database Migrations

If you want to create a new table or modify an existing one you will need to create an alembic migration. Most of the time, you can do this by autogenerating it.

First, create the table definition in tuber/models/<name>.py, and make sure it is imported in tuber/models/__init__.py.

Next, use alembic to create the migration file:

```bash
venv/bin/alembic revision --autogenerate -m "Added widget column to the whatsit table"
```

This should create a migration file in migrations/versions. Read through it and adjust the steps as necessary. The next time you restart your dev instance it will run the migration.

You can also trigger the database update manually:
```bash
venv/bin/alembic upgrade head
```

Make sure to commit the migration along with the code that uses it!

### Troubleshooting
#### Mac developer setup

If you receive the following ambiguous error message: `ld: library not found for -lssl`

The fix for this: `export LDFLAGS="-L/usr/local/opt/openssl/lib"`

#### Alembic with multiple heads

Sometimes when merging a branch that has its own new migrations into your own branch you'll have to tell alembic what to do.
If you see alembic complaining about multiple heads check here: https://blog.jerrycodes.com/multiple-heads-in-alembic-migrations/