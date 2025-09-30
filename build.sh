#!/usr/bin/env bash
set -o errexit

# Create data directory in persistent location
mkdir -p /opt/render/project/src/data

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Initialize SQLite database
python -c "
import model
import os
os.makedirs('data', exist_ok=True)
model.init_db()
model.seed_default_categories()
print('✅ SQLite database initialized')
"
