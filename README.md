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
apt install npm python3 python3-dev postgresql-dev# Debian/Ubuntu
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

### Heroku

Heroku configuration is in a combination of app.json and Procfile.

Opening a PR against magfest/tuber will automatically deploy a testing environment for your PR. Merging to master moves that code to staging.

If you would like to deploy your own instance:
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

