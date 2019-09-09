Name: {{{ git_name tuber }}}
Version: {{{ git_dir_version }}}
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
Requires: python1-flask-migrate

%{?python_enable_dependency_generator}

%description
Tuber is an event management system.

%prep
{{{ git_dir_setup_macro }}}

%build
cd ./server
%py3_build
cd ..
npm install
npm run build

%install
cd ./server
%py3_install
cd ..
mkdir -p %{buildroot}/usr/lib/systemd/system
cp server/contrib/tuber.service %{buildroot}/usr/lib/systemd/system/
mkdir -p %{buildroot}/usr/share/tuber/web/js/
mkdir -p %{buildroot}/usr/share/tuber/web/css/
cp dist/js/app.*.js %{buildroot}/usr/share/tuber/web/
cp dist/js/chunk-vendors.*.js %{buildroot}/usr/share/tuber/web/js/
cp dist/css/app.*.css %{buildroot}/usr/share/tuber/web/css/
cp dist/css/chunk-vendors.*.css %{buildroot}/usr/share/tuber/web/css/
cp dist/index.html %{buildroot}/usr/share/tuber/web/
cp dist/favicon.ico %{buildroot}/usr/share/tuber/web/
mkdir -p %{buildroot}/usr/share/tuber/migrations/
cp -r migrations/* %{buildroot}/usr/share/tuber/migrations/
mkdir -p %{buildroot}/etc/tuber
cp server/contrib/tuber.conf %{buildroot}/etc/tuber/

%files
%config /etc/tuber/tuber.conf
/usr/lib/systemd/system/tuber.service
/usr/bin/tuber
/usr/share/tuber
%{python3_sitearch}/tuber/
%{python3_sitearch}/tuber-*.egg-info/

%changelog
{{{ git_dir_changelog }}}