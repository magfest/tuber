all: build

build: venv node_modules
	venv/bin/python setup.py build
	npm run build

node_modules: package.json
	npm install

install-develop: venv node_modules
	venv/bin/python setup.py develop

develop: install-develop tuber.json
	node_modules/.bin/kill-port 8081 8080
	npm run serve &
	FLASK_ENV=development venv/bin/tuber --config tuber.json

tuber.json:
	cp contrib/tuber.json.devel tuber.json
	echo "Copied default tuber.json from contrib/tuber.json. Feel free to edit it to your heart's content."

venv: venv/bin/activate

venv/bin/activate:
	python3 -m venv venv
	echo "export FLASK_APP=tuber" >> venv/bin/activate

test: build pytest
	venv/bin/pytest
	npm run test

pytest: venv/bin/pytest

venv/bin/pytest: venv
	venv/bin/pip install -r requirements-test.txt

rpm: venv node_modules
	-rm -rf dist
	npm run build
	/usr/bin/env python3 setup.py bdist_rpm --release $(shell git rev-list $(shell git tag)..HEAD --count)

deb: rpm
	fpm -s rpm -t deb dist/tuber*.noarch.rpm

.PHONY: clean
clean:
	-rm -rf venv
	-rm -rf tuber.egg-info
	-rm -rf build
	-rm -rf dist
	-rm -rf node_modules
	-rm -rf web
	-rm *.deb
