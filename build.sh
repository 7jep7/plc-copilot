#!/bin/bash

# Build script for Render deployment

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Running database migrations..."
alembic upgrade head

echo "Creating upload directory..."
mkdir -p /opt/render/project/src/uploads

echo "Build completed successfully!"