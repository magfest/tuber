#!/bin/bash

set -e

cd backend
CIRCUITBREAKER_TIMEOUT=60 ENABLE_CIRCUITBREAKER=false coverage run --source=tuber -m pytest
bash <(curl -s https://codecov.io/bash) -C $HEROKU_TEST_RUN_COMMIT_VERSION

cd ../frontend
npm run test