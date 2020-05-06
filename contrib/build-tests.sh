#!/bin/bash
cd ../
python -m venv venv
cd backend
../venv/bin/python setup.py install
../venv/bin/pip install pytest

cd ../frontend
npm install