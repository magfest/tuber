# Tuber

[![Copr build status](https://copr.fedorainfracloud.org/coprs/bitbyt3r/Tuber/package/tuber/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/bitbyt3r/Tuber/package/tuber/)
[![Heroku CI Status](https://tuber-ci-badge.herokuapp.com/last.svg)](https://dashboard.heroku.com/pipelines/6ebd065d-db02-419d-80bd-6406f271d992/tests)

## Installation

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

Configuration is in /etc/tuber/tuber.json. The main configuration required is for a database. The default database is sqlite, so for production deploys you should probably set up mariadb/mysql/postgres or any other database supported by SQLAlchemy.

## Developing

After cloning this repository you will need the following dependencies:

```bash
dnf install npm python3 python3-devel postgresql-devel # Fedora/RHEL/CentOS
apt install npm python3 python3-dev python3-pip libpq-dev # Debian/Ubuntu
brew install npm python postgresql # MacOS
```

Once you have the dependencies you can simply run make to build, then make develop to run the test server:

```bash
make develop
```

You can run the tests using make test, though you will need to install pytest first:

```bash
venv/bin/pip install pytest
make test
```

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

### Heroku

Heroku configuration is in a combination of app.json and Procfile.

Opening a PR against magfest/tuber will automatically deploy a testing environment for your PR. Merging to master moves that code to staging.

If you would like to deploy your own instance:
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### Troubleshooting
#### Mac developer setup

If you receive the following ambiguous error message: `ld: library not found for -lssl`

The fix for this: `export LDFLAGS="-L/usr/local/opt/openssl/lib"`

#### Alembic with multiple heads

Sometimes when merging a branch that has its own new migrations into your own branch you'll have to tell alembic what to do.
If you see alembic complaining about multiple heads check here: https://blog.jerrycodes.com/multiple-heads-in-alembic-migrations/