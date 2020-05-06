#!/bin/bash

venv/bin/activate
cd backend
pytest

cd ../frontend
npm run test