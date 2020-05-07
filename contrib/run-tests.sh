#!/bin/bash

set -e

cd backend
pytest

cd ../frontend
npm run test