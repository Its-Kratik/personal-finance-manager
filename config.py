#!/usr/bin/env python3
"""
Personal Finance Manager Pro - Configuration Management
======================================================

Centralized configuration management for the application with:
- Environment-based settings
- Security configurations
- Feature toggles

Version: 1.0.0
Author: Finance Manager Team
License: MIT
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class with common settings."""
    
    # Application Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Configuration
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'data/finance.db')
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(
        hours=int(os.environ.get('SESSION_TIMEOUT_HOURS', 24))
    )
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Security Settings
    FORCE_HTTPS = os.environ.get('FORCE_HTTPS', 'True').lower() == 'true'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Rate Limiting
    RATE_LIMIT_STORAGE = os.environ.get('RATE_LIMIT_STORAGE_URL', 'memory://')
    
    # File Upload Settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'csv', 'json', 'txt'}
    
    # Email Settings (optional)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Feature Flags
    ENABLE_REGISTRATION = os.environ.get('ENABLE_REGISTRATION', 'True').lower() == 'true'
    ENABLE_EMAIL_VERIFICATION = os.environ.get('ENABLE_EMAIL_VERIFICATION', 'False').lower() == 'true'
    ENABLE_PASSWORD_RESET = os.environ.get('ENABLE_PASSWORD_RESET', 'False').lower() == 'true'
    ENABLE_EXPORT = os.environ.get('ENABLE_EXPORT', 'True').lower() == 'true'
    
    # Pagination
    TRANSACTIONS_PER_PAGE = int(os.environ.get('TRANSACTIONS_PER_PAGE', 50))
    MAX_SEARCH_RESULTS = int(os.environ.get('MAX_SEARCH_RESULTS', 100))
    
    # Cache Settings
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    
    @staticmethod
    def init_app(app):
        """Initialize application configuration."""
        # Ensure folders exist
        import os
        os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True
    FORCE_HTTPS = False
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    FORCE_HTTPS = True
    SESSION_COOKIE_SECURE = True
    
    @classmethod
    def init_app(cls, app):
        super().init_app(app)
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

class TestingConfig(Config):
    TESTING = True
    DATABASE_PATH = ':memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
