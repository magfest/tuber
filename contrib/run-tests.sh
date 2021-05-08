#!/bin/bash

set -e

CIRCUITBREAKER_TIMEOUT=60
cd backend
coverage run --source=tuber -m pytest
bash <(curl -s https://codecov.io/bash) -C $HEROKU_TEST_RUN_COMMIT_VERSION

cd ../frontend
npm run test