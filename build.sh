#!/usr/bin/env bash
# Render build script

set -o errexit  # exit on error

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Initialize database (for PostgreSQL)
python -c "
import model
try:
    model.init_db()
    model.seed_default_categories() 
    print('Database initialized')
except Exception as e:
    print(f'Database init: {e}')
"
