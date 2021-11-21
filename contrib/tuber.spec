Name: {{{ git_name tuber }}}
Version: {{{ git_version name=tuber }}}
Release: 1%{?dist}
Summary: Event Management System
License: MIT
URL: https://tuber.hackafe.net/
VCS: {{{ git_dir_vcs }}}
Source: {{{ git_pack }}}
BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: python3-pip
BuildRequires: npm
BuildRequires: git
Requires: python3-passlib
Requires: python3-flask
Requires: python3-requests
Requires: python3-gunicorn
Requires: python3-alembic
Requires: python3-redis
Requires: python3-lupa
Requires: python3-boto3
Requires: python3-jinja2
Requires: python3-psycopg2

%define  debug_package %{nil}
%{?python_enable_dependency_generator}

%description
Tuber is an event management system.

%prep
{{{ git_dir_setup_macro }}}

%build
cd backend
%py3_build
cd ../frontend
npm install --legacy-peer-deps
npm run build

%install
cd backend
%py3_install
cd ..
mkdir -p %{buildroot}/usr/lib/systemd/system
mkdir -p %{buildroot}/var/lib/tuber/
mkdir -p %{buildroot}/usr/share/tuber/web/js/
mkdir -p %{buildroot}/usr/share/tuber/web/css/
mkdir -p %{buildroot}/usr/share/tuber/migrations/
mkdir -p %{buildroot}/etc/tuber
mkdir -p %{buildroot}/etc/default
cp contrib/nginx.conf.rhel %{buildroot}/usr/share/tuber/nginx.conf
cp contrib/tuber.service %{buildroot}/usr/lib/systemd/system/
cp contrib/tuber %{buildroot}/etc/default/
cp frontend/dist/js/app.*.js %{buildroot}/usr/share/tuber/web/js/
cp frontend/dist/js/chunk-vendors.*.js %{buildroot}/usr/share/tuber/web/js/
cp frontend/dist/css/app.*.css %{buildroot}/usr/share/tuber/web/css/
cp frontend/dist/css/chunk-vendors.*.css %{buildroot}/usr/share/tuber/web/css/
cp frontend/dist/index.html %{buildroot}/usr/share/tuber/web/
cp frontend/dist/favicon.ico %{buildroot}/usr/share/tuber/web/
cp -r backend/migrations/* %{buildroot}/usr/share/tuber/migrations/

%files
%config /etc/default/tuber
/usr/lib/systemd/system/tuber.service
/usr/bin/tuber
/usr/share/tuber
%{python3_sitelib}/tuber/
%{python3_sitelib}/tuber-*.egg-info/
%dir /var/lib/tuber

%changelog
{{{ git_dir_changelog }}}