#!/bin/bash

cd backend
pytest

cd ../frontend
npm run test