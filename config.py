import os

class Config:
    # Render provides these automatically
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-me')
    
    # Use Render's DATABASE_URL for PostgreSQL
    DATABASE_URL = os.environ.get('DATABASE_URL')
    DATABASE_PATH = 'data/finance.db'  # Local dev fallback
    
    # Render handles HTTPS automatically
    FORCE_HTTPS = os.environ.get('RENDER_EXTERNAL_URL') is not None
    
    # Session settings for production
    SESSION_COOKIE_SECURE = True if os.environ.get('RENDER_EXTERNAL_URL') else False
    
    # Render doesn't need file-based rate limiting
    RATE_LIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    
    # Use Render's PORT environment variable
    PORT = int(os.environ.get('PORT', 5000))
# Add this to config.py
class FreeConfig(Config):
    """Free deployment configuration"""
    # Force SQLite for free tier
    DATABASE_URL = None
    DATABASE_PATH = '/opt/render/project/src/data/finance.db'
    
    # Free tier settings
    FORCE_HTTPS = False  # Free tier doesn't get custom SSL
    SESSION_COOKIE_SECURE = False
