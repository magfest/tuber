all: build

build: venv node_modules
	cd server && ../venv/bin/python setup.py develop

node_modules: package.json
	npm install

develop: build tuber.conf
	node_modules/.bin/kill-port 8081 8080
	npm run serve &
	FLASK_ENV=development venv/bin/tuber --config tuber.json

tuber.json:
	cp server/contrib/tuber.json.devel tuber.json
	echo "Copied default tuber.json from server/contrib/tuber.json. Feel free to edit it to your heart's content."

venv: venv/bin/activate

venv/bin/activate:
	python3 -m venv venv
	echo "export FLASK_APP=tuber" >> venv/bin/activate

test: build
	venv/bin/pytest
	npm run test:unit
	npm run test:e2e

rpm: venv node_modules
	-rm -rf dist
	npm run build
	-rm -rf server/web/*
	-mkdir server/web
	cp -r dist/* server/web/
	cp -r migrations server/
	-find server/ -type d -name __pycache__ -delete
	cd server && /usr/bin/env python3 setup.py bdist_rpm --release $(shell git rev-list $(shell git tag)..HEAD --count)

.PHONY: clean
clean:
	-rm -rf venv
	-rm -rf server/tuber.egg-info
	-rm -rf server/build
	-rm -rf server/dist
	-rf -rf server/migrations
	-rm -rf node_modules
	-rm -rf server/web
