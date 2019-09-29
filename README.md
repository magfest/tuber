# 2ber
[![Copr build status](https://copr.fedorainfracloud.org/coprs/bitbyt3r/Tuber/package/tuber/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/bitbyt3r/Tuber/package/tuber/)

## Installation
This software is currently only packaged for RHEL/Fedora. Builds are available on COPR:
```
dnf copr enable bitbyt3r/Tuber
dnf install copr
systemctl start copr
systemctl enable copr
cp /usr/share/tuber/nginx.conf /etc/nginx/conf.d/tuber.conf
systemctl start nginx
systemctl enable nginx
```

You can also run tuber directly on the command line to use the built in webserver, but this is not recommended for production deploys:
```
dnf copr enable bitbyt3r/Tuber
dnf install copr
tuber
```

Configuration is in /etc/tuber/tuber.json. The main configuration required is for a database. The default database is sqlite, so for production deploys you should probably set up mariadb/mysql/postgres or any other database supported by SQLAlchemy.

## Developing
After cloning this repository you will need the following dependencies:
```
dnf install npm python3
apt install npm python3
```

Once you have the dependencies you can simply run make to build, then make develop to run the test server:
```
make
make develop
```

You can run the tests using make test, though you will need to install pytest first:
```
dnf install python3-pytest
make test
```

## Project setup
```
npm install
```

### Compiles and hot-reloads for development
```
npm run serve
```

### Compiles and minifies for production
```
npm run build
```

### Run your tests
```
npm run test
```

### Lints and fixes files
```
npm run lint
```

### Run your end-to-end tests
```
npm run test:e2e
```

### Run your unit tests
```
npm run test:unit
```

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).

### Heroku
Heroku configuration is in a combination of app.json and Procfile.

Opening a PR against magfest/tuber will automatically deploy a testing environment for your PR. Merging to master moves that code to staging.
