Name: {{{ git_name tuber }}}
Version: {{{ git_version name=tuber }}}
Release: 1%{?dist}
Summary: Event Management System
License: MIT
URL: https://tuber.hackafe.net/
VCS: {{{ git_dir_vcs }}}
Source: {{{ git_dir_pack }}}
BuildRequires: python3-devel
BuildRequires: npm
BuildRequires: git
Requires: python3-passlib
Requires: python3-flask
Requires: python3-requests
Requires: python3-gunicorn
Requires: python3-flask-sqlalchemy
Requires: python3-flask-migrate

%define  debug_package %{nil}
%{?python_enable_dependency_generator}

%description
Tuber is an event management system.

%prep
{{{ git_dir_setup_macro }}}

%build
echo FINDING
find
echo PWDING
pwd
echo LSING
ls ../
cd ../backend
%py3_build
cd ../frontend
npm install
npm run build

%install
%py3_install
mkdir -p %{buildroot}/usr/lib/systemd/system
mkdir -p %{buildroot}/var/lib/tuber/
mkdir -p %{buildroot}/usr/share/tuber/web/js/
mkdir -p %{buildroot}/usr/share/tuber/web/css/
mkdir -p %{buildroot}/usr/share/tuber/migrations/
mkdir -p %{buildroot}/etc/tuber
cp contrib/nginx.conf %{buildroot}/usr/share/tuber/nginx.conf
cp contrib/tuber.service %{buildroot}/usr/lib/systemd/system/
cp contrib/tuber.json %{buildroot}/etc/tuber/
cp contrib/tuber.json %{buildroot}/usr/share/tuber/
cp frontend/dist/js/app.*.js %{buildroot}/usr/share/tuber/web/js/
cp frontend/dist/js/chunk-vendors.*.js %{buildroot}/usr/share/tuber/web/js/
cp frontend/dist/css/app.*.css %{buildroot}/usr/share/tuber/web/css/
cp frontend/dist/css/chunk-vendors.*.css %{buildroot}/usr/share/tuber/web/css/
cp frontend/dist/index.html %{buildroot}/usr/share/tuber/web/
cp frontend/dist/favicon.ico %{buildroot}/usr/share/tuber/web/
cp -r backend/migrations/* %{buildroot}/usr/share/tuber/migrations/

%files
%config /etc/tuber/tuber.json
/usr/lib/systemd/system/tuber.service
/usr/bin/tuber
/usr/share/tuber
%{python3_sitelib}/tuber/
%{python3_sitelib}/tuber-*.egg-info/
%dir /var/lib/tuber

%changelog
{{{ git_dir_changelog }}}