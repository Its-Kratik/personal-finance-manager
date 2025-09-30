#!/usr/bin/env bash
# Render build script

set -o errexit  # exit on error

echo "Starting build process..."

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "Dependencies installed successfully"

# Initialize database
echo "Initializing database..."
python -c "
import model
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    logger.info('Initializing database...')
    model.init_db()
    logger.info('Database initialized successfully')
    
    logger.info('Seeding default categories...')
    model.seed_default_categories()
    logger.info('Default categories seeded successfully')
    
    print('✅ Database setup completed successfully')
except Exception as e:
    logger.error(f'Database setup failed: {e}')
    print(f'❌ Database setup failed: {e}')
    # Don't exit - let Render handle this gracefully
"

echo "Build completed successfully!"
