#!/usr/bin/env python3
"""
Personal Finance Manager Pro - Main Application Controller (Render Compatible)
"""

import os
import json
import logging
import hashlib
import secrets
import time
import re
from datetime import datetime, date, timedelta
from functools import wraps
from typing import Dict, Any, Optional, List

from flask import Flask, request, jsonify, session, render_template, Response, abort
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import RequestEntityTooLarge
import bleach
import html

import model
from config import Config

# ✅ RENDER-OPTIMIZED LOGGING CONFIGURATION
def setup_logging():
    """Setup logging for Render deployment"""
    
    # Render captures stdout/stderr automatically, so we only log to console
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()  # Only console output for Render
        ],
        force=True  # Override any existing configuration
    )
    
    # Set specific loggers
    logger = logging.getLogger(__name__)
    
    # Suppress noisy third-party logs in production
    if os.environ.get('FLASK_ENV') == 'production':
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger.info("Logging configured for Render deployment")
    return logger

# Initialize logging
logger = setup_logging()

# Initialize Flask application
app = Flask(__name__)

# Render-specific configuration
class RenderConfig(Config):
    """Configuration optimized for Render deployment"""
    
    # Render sets PORT automatically
    PORT = int(os.environ.get('PORT', 5000))
    
    # Render handles HTTPS automatically
    FORCE_HTTPS = os.environ.get('RENDER_EXTERNAL_URL') is not None
    
    # Secure cookies in production
    SESSION_COOKIE_SECURE = bool(os.environ.get('RENDER_EXTERNAL_URL'))
    
    # Use Redis if available, otherwise memory
    RATE_LIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')

# Apply Render configuration
app.config.from_object(RenderConfig)

# Security Headers with Talisman
csp = {
    'default-src': "'self'",
    'script-src': [
        "'self'",
        "'unsafe-inline'",  # Required for Chart.js
        'cdn.jsdelivr.net',
        'https://fonts.googleapis.com'
    ],
    'style-src': [
        "'self'",
        "'unsafe-inline'",  # Required for dynamic styles
        'fonts.googleapis.com'
    ],
    'font-src': [
        "'self'",
        'fonts.gstatic.com'
    ],
    'img-src': [
        "'self'",
        'data:',
        'blob:'
    ],
    'connect-src': "'self'",
}

# Initialize security features
Talisman(app, 
    force_https=app.config['FORCE_HTTPS'],
    strict_transport_security=True,
    content_security_policy=csp,
    feature_policy={
        'geolocation': "'none'",
        'camera': "'none'",
        'microphone': "'none'",
    }
)

# Rate Limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"],
    storage_uri=app.config.get('RATE_LIMIT_STORAGE_URL', 'memory://')
)

# Utility Functions
def sanitize_input(data: Any) -> Any:
    """
    Sanitize user input to prevent XSS attacks.
    
    Args:
        data: Input data to sanitize
        
    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        # Remove HTML tags and encode special characters
        sanitized = bleach.clean(data, tags=[], strip=True)
        return html.escape(sanitized)
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data

def validate_amount(amount: Any) -> float:
    """Validate and convert amount to float."""
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            raise ValueError("Amount must be positive")
        if amount_float > 1000000:  # Max $1M per transaction
            raise ValueError("Amount exceeds maximum limit")
        return round(amount_float, 2)
    except (TypeError, ValueError) as e:
        logger.warning(f"Invalid amount provided: {amount}")
        raise ValueError(f"Invalid amount: {str(e)}")

def validate_date(date_str: str) -> str:
    """Validate date format and range."""
    try:
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Don't allow dates too far in the future
        max_future_date = date.today() + timedelta(days=30)
        if parsed_date > max_future_date:
            raise ValueError("Date cannot be more than 30 days in the future")
            
        # Don't allow dates too far in the past
        min_past_date = date.today() - timedelta(days=3650)
        if parsed_date < min_past_date:
            raise ValueError("Date cannot be more than 10 years in the past")
            
        return date_str
    except ValueError as e:
        logger.warning(f"Invalid date provided: {date_str}")
        raise ValueError(f"Invalid date: {str(e)}")

# Authentication Decorators
def login_required(f):
    """Require user authentication for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.info(f"Unauthorized access attempt to {request.endpoint}")
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def log_user_action(action: str):
    """Decorator to log user actions for debugging and auditing."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id', 'anonymous')
            ip_address = request.remote_addr
            
            logger.info(f"User {user_id} performed {action} from {ip_address}")
            
            try:
                result = f(*args, **kwargs)
                logger.info(f"Action {action} completed successfully for user {user_id}")
                return result
            except Exception as e:
                logger.error(f"Action {action} failed for user {user_id}: {str(e)}")
                raise
        return decorated_function
    return decorator

# Error Handlers
@app.errorhandler(400)
def bad_request(error):
    logger.warning(f"Bad request: {request.url} - {str(error)}")
    return jsonify({'error': 'Bad request', 'message': 'Invalid request data'}), 400

@app.errorhandler(401)
def unauthorized(error):
    logger.warning(f"Unauthorized access: {request.url}")
    return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401

@app.errorhandler(404)
def not_found(error):
    logger.info(f"Page not found: {request.url}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404
    return render_template('index.html'), 404

@app.errorhandler(429)
def ratelimit_handler(e):
    logger.warning(f"Rate limit exceeded: {request.remote_addr}")
    return jsonify({'error': 'Rate limit exceeded', 'message': 'Too many requests'}), 429

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error', 'message': 'Something went wrong'}), 500

# Database Initialization
@app.before_first_request
def initialize_database():
    """Initialize database and seed default data."""
    try:
        model.init_db()
        model.seed_default_categories()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.critical(f"Database initialization failed: {str(e)}")
        raise

# Security Headers
@app.after_request
def after_request(response):
    """Add security headers and caching for static assets."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Cache static assets
    if request.endpoint and request.endpoint.startswith('static'):
        response.headers['Cache-Control'] = 'public, max-age=31536000'
        response.headers['Expires'] = (datetime.now() + timedelta(days=365)).strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    return response

# Routes
@app.route('/')
def index():
    """Landing page."""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
@log_user_action("login_attempt")
def login():
    """Handle user login with comprehensive security measures."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = sanitize_input(data.get('username', '').strip())
        password = data.get('password', '')
        
        if not username or not password:
            logger.warning(f"Login attempt with missing credentials from {request.remote_addr}")
            time.sleep(1)  # Prevent timing attacks
            return jsonify({'error': 'Username and password are required'}), 400
        
        if len(username) > 50 or len(password) > 128:
            return jsonify({'error': 'Invalid input length'}), 400
        
        user = model.get_user_by_username(username)
        
        if user and check_password_hash(user['password_hash'], password):
            session.regenerate()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session.permanent = True
            
            model.update_last_login(user['id'])
            
            logger.info(f"Successful login for user {username}")
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': sanitize_input(user['email'])
                }
            })
        else:
            logger.warning(f"Failed login attempt for user {username}")
            time.sleep(1)  # Prevent timing attacks
            return jsonify({'error': 'Invalid username or password'}), 401
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/register', methods=['POST'])
@limiter.limit("3 per minute")
@log_user_action("registration_attempt")
def register():
    """Handle user registration with comprehensive validation."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = sanitize_input(data.get('username', '').strip())
        email = sanitize_input(data.get('email', '').strip().lower())
        password = data.get('password', '')
        
        # Validation
        if not all([username, email, password]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Username validation
        if len(username) < 3 or len(username) > 50:
            return jsonify({'error': 'Username must be 3-50 characters'}), 400
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return jsonify({'error': 'Username can only contain letters, numbers, - and _'}), 400
        
        # Email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Password validation
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
            return jsonify({'error': 'Password must contain both letters and numbers'}), 400
        
        # Check if user exists
        if model.get_user_by_username(username):
            return jsonify({'error': 'Username already exists'}), 400
        
        if model.get_user_by_email(email):
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create user
        password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        user_id = model.create_user(username, email, password_hash)
        
        if user_id:
            session.regenerate()
            session['user_id'] = user_id
            session['username'] = username
            session.permanent = True
            
            logger.info(f"New user registered: {username}")
            
            return jsonify({
                'success': True,
                'message': 'Registration successful',
                'user': {
                    'id': user_id,
                    'username': username,
                    'email': email
                }
            })
        else:
            return jsonify({'error': 'Registration failed'}), 500
            
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/logout')
@log_user_action("logout")
def logout():
    """Handle user logout with secure session cleanup."""
    user_id = session.get('user_id')
    session.clear()
    
    if user_id:
        logger.info(f"User {user_id} logged out")
    
    return jsonify({'success': True, 'message': 'Logged out successfully'})

# Protected Routes
@app.route('/dashboard')
@login_required
@log_user_action("dashboard_visit")
def dashboard():
    """Main dashboard."""
    model.update_onboarding_progress(session['user_id'], {'dashboard_visited': True})
    return render_template('index.html')

@app.route('/transactions', methods=['GET', 'POST'])
@login_required
@limiter.limit("100 per minute")
def transactions():
    """Handle transaction operations."""
    user_id = session['user_id']
    
    if request.method == 'GET':
        try:
            # Get and validate filters
            filters = {
                'type': sanitize_input(request.args.get('type', 'all')),
                'category_id': request.args.get('category_id'),
                'start_date': request.args.get('start_date'),
                'end_date': request.args.get('end_date'),
                'sort_by': sanitize_input(request.args.get('sort_by', 'date_desc'))
            }
            
            # Validate dates
            if filters['start_date']:
                filters['start_date'] = validate_date(filters['start_date'])
            if filters['end_date']:
                filters['end_date'] = validate_date(filters['end_date'])
            
            # Validate category_id
            if filters['category_id']:
                try:
                    filters['category_id'] = int(filters['category_id'])
                except ValueError:
                    return jsonify({'error': 'Invalid category ID'}), 400
            
            filters = {k: v for k, v in filters.items() if v and v != 'all'}
            
            transactions = model.get_transactions(user_id, filters)
            
            transaction_list = []
            for transaction in transactions:
                transaction_list.append({
                    'id': transaction['id'],
                    'amount': float(transaction['amount']),
                    'type': sanitize_input(transaction['type']),
                    'description': sanitize_input(transaction['description'] or ''),
                    'date': transaction['date'],
                    'category_id': transaction['category_id'],
                    'category_name': sanitize_input(transaction['category_name']),
                    'created_at': transaction['created_at']
                })
            
            return jsonify({'transactions': transaction_list})
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error fetching transactions for user {user_id}: {str(e)}")
            return jsonify({'error': 'Failed to fetch transactions'}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validate inputs
            amount = validate_amount(data.get('amount'))
            transaction_type = sanitize_input(data.get('type', '')).lower()
            category_id = int(data.get('category_id', 0))
            date_str = validate_date(data.get('date', ''))
            description = sanitize_input(data.get('description', ''))[:200]
            
            if transaction_type not in ['income', 'expense']:
                return jsonify({'error': 'Type must be income or expense'}), 400
            
            # Validate category
            category = model.get_category_by_id(category_id)
            if not category or category['type'] != transaction_type:
                return jsonify({'error': 'Invalid category'}), 400
            
            # Add transaction
            transaction_id = model.add_transaction(
                user_id=user_id,
                category_id=category_id,
                amount=amount,
                transaction_type=transaction_type,
                description=description,
                date=date_str
            )
            
            if transaction_id:
                model.update_onboarding_progress(user_id, {'first_transaction_added': True})
                logger.info(f"Transaction added: ID {transaction_id} for user {user_id}")
                
                return jsonify({
                    'success': True,
                    'message': 'Transaction added successfully',
                    'transaction_id': transaction_id
                })
            else:
                return jsonify({'error': 'Failed to add transaction'}), 500
                
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Transaction creation error: {str(e)}")
            return jsonify({'error': 'Failed to add transaction'}), 500

@app.route('/transactions/<int:transaction_id>', methods=['PUT', 'DELETE'])
@login_required
def transaction_detail(transaction_id):
    """Handle individual transaction operations."""
    user_id = session['user_id']
    
    if request.method == 'PUT':
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['amount', 'type', 'category_id', 'date']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'{field} is required'}), 400
            
            # Validate amount
            amount = validate_amount(data.get('amount'))
            
            # Validate type
            transaction_type = sanitize_input(data.get('type', '')).lower()
            if transaction_type not in ['income', 'expense']:
                return jsonify({'error': 'Type must be income or expense'}), 400
            
            # Update transaction
            success = model.update_transaction(transaction_id, user_id, {
                'amount': amount,
                'type': transaction_type,
                'category_id': data['category_id'],
                'description': sanitize_input(data.get('description', '')),
                'date': validate_date(data['date'])
            })
            
            if success:
                return jsonify({'success': True, 'message': 'Transaction updated successfully'})
            else:
                return jsonify({'error': 'Transaction not found or access denied'}), 404
                
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Failed to update transaction'}), 500
    
    elif request.method == 'DELETE':
        try:
            success = model.delete_transaction(transaction_id, user_id)
            
            if success:
                return jsonify({'success': True, 'message': 'Transaction deleted successfully'})
            else:
                return jsonify({'error': 'Transaction not found or access denied'}), 404
                
        except Exception as e:
            return jsonify({'error': 'Failed to delete transaction'}), 500

# Search functionality
@app.route('/api/search/transactions')
@login_required
def search_transactions():
    """Search transactions."""
    try:
        user_id = session['user_id']
        search_term = request.args.get('q', '').strip()
        
        if not search_term:
            return jsonify({'transactions': [], 'count': 0})
        
        # Get additional filters
        filters = {
            'type': request.args.get('type', 'all'),
            'category_id': request.args.get('category_id'),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date')
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v and v != 'all'}
        
        transactions = model.search_transactions(user_id, search_term, filters)
        
        # Convert to list of dicts
        transaction_list = []
        for transaction in transactions:
            transaction_list.append({
                'id': transaction['id'],
                'amount': transaction['amount'],
                'type': transaction['type'],
                'description': transaction['description'],
                'date': transaction['date'],
                'category_id': transaction['category_id'],
                'category_name': transaction['category_name'],
                'category_icon': transaction['category_icon'],
                'created_at': transaction['created_at']
            })
        
        return jsonify({
            'transactions': transaction_list,
            'count': len(transaction_list),
            'search_term': search_term
        })
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

# Export functionality
@app.route('/api/export/transactions')
@login_required
def export_transactions():
    """Export transactions to CSV."""
    try:
        user_id = session['user_id']
        
        # Get filters from request
        filters = {
            'type': request.args.get('type', 'all'),
            'category_id': request.args.get('category_id'),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date'),
            'sort_by': request.args.get('sort_by', 'date_desc')
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v and v != 'all'}
        
        csv_data = model.export_transactions_csv(user_id, filters)
        
        if not csv_data:
            return jsonify({'error': 'No data to export'}), 400
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'transactions_{timestamp}.csv'
        
        response = Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
        # Update onboarding progress
        model.update_onboarding_progress(user_id, {'export_used': True})
        
        return response
        
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500

# Budget management
@app.route('/api/budgets', methods=['GET', 'POST'])
@login_required
def budgets():
    """Handle budget operations."""
    user_id = session['user_id']
    
    if request.method == 'GET':
        try:
            budgets = model.get_user_budgets(user_id)
            budget_list = []
            
            for budget in budgets:
                budget_list.append({
                    'id': budget['id'],
                    'category_id': budget['category_id'],
                    'category_name': budget['category_name'],
                    'category_icon': budget['category_icon'],
                    'category_color': budget['category_color'],
                    'amount': budget['amount'],
                    'period': budget['period'],
                    'start_date': budget['start_date'],
                    'is_active': budget['is_active']
                })
            
            return jsonify({'budgets': budget_list})
            
        except Exception as e:
            logger.error(f"Failed to fetch budgets: {str(e)}")
            return jsonify({'error': 'Failed to fetch budgets'}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validate required fields
            if not all(key in data for key in ['category_id', 'amount', 'period']):
                return jsonify({'error': 'Missing required fields'}), 400
            
            amount = validate_amount(data['amount'])
            
            budget_id = model.create_budget(
                user_id=user_id,
                category_id=data['category_id'],
                amount=amount,
                period=data['period'],
                start_date=data.get('start_date')
            )
            
            if budget_id:
                # Update onboarding progress
                model.update_onboarding_progress(user_id, {'first_budget_set': True})
                
                return jsonify({
                    'success': True,
                    'message': 'Budget created successfully',
                    'budget_id': budget_id
                })
            else:
                return jsonify({'error': 'Failed to create budget'}), 500
                
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Failed to create budget: {str(e)}")
            return jsonify({'error': 'Failed to create budget'}), 500

@app.route('/api/budgets/performance')
@login_required
def budget_performance():
    """Get budget performance data."""
    try:
        user_id = session['user_id']
        period = request.args.get('period', 'monthly')
        
        performance_data = model.get_budget_performance(user_id, period)
        
        return jsonify({
            'performance': performance_data,
            'period': period
        })
        
    except Exception as e:
        logger.error(f"Failed to fetch budget performance: {str(e)}")
        return jsonify({'error': 'Failed to fetch budget performance'}), 500

# User preferences
@app.route('/api/preferences', methods=['GET', 'PUT'])
@login_required
def user_preferences():
    """Handle user preferences."""
    user_id = session['user_id']
    
    if request.method == 'GET':
        try:
            preferences = model.get_user_preferences(user_id)
            
            if preferences:
                return jsonify({
                    'preferences': {
                        'currency': preferences['currency'],
                        'date_format': preferences['date_format'],
                        'theme': preferences['theme'],
                        'default_view': preferences['default_view'],
                        'timezone': preferences['timezone'],
                        'language': preferences['language'],
                        'notifications_enabled': preferences['notifications_enabled'],
                        'export_format': preferences['export_format']
                    }
                })
            else:
                return jsonify({'error': 'Preferences not found'}), 404
                
        except Exception as e:
            logger.error(f"Failed to fetch preferences: {str(e)}")
            return jsonify({'error': 'Failed to fetch preferences'}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            success = model.update_user_preferences(user_id, data)
            
            if success:
                return jsonify({'success': True, 'message': 'Preferences updated successfully'})
            else:
                return jsonify({'error': 'Failed to update preferences'}), 400
                
        except Exception as e:
            logger.error(f"Failed to update preferences: {str(e)}")
            return jsonify({'error': 'Failed to update preferences'}), 500

# Transaction insights
@app.route('/api/insights')
@login_required
def transaction_insights():
    """Get transaction insights and analytics."""
    try:
        user_id = session['user_id']
        period_days = int(request.args.get('days', 30))
        
        insights = model.get_transaction_insights(user_id, period_days)
        
        return jsonify({'insights': insights})
        
    except Exception as e:
        logger.error(f"Failed to fetch insights: {str(e)}")
        return jsonify({'error': 'Failed to fetch insights'}), 500

# Onboarding
@app.route('/api/onboarding', methods=['GET', 'PUT'])
@login_required
def onboarding():
    """Handle user onboarding."""
    user_id = session['user_id']
    
    if request.method == 'GET':
        try:
            onboarding_data = model.get_user_onboarding(user_id)
            
            if onboarding_data:
                return jsonify({
                    'onboarding': {
                        'tour_completed': onboarding_data['tour_completed'],
                        'sample_data_added': onboarding_data['sample_data_added'],
                        'first_transaction_added': onboarding_data['first_transaction_added'],
                        'first_budget_set': onboarding_data['first_budget_set'],
                        'dashboard_visited': onboarding_data['dashboard_visited'],
                        'reports_visited': onboarding_data['reports_visited'],
                        'checklist_completed': onboarding_data['checklist_completed']
                    }
                })
            else:
                return jsonify({'error': 'Onboarding data not found'}), 404
                
        except Exception as e:
            logger.error(f"Failed to fetch onboarding data: {str(e)}")
            return jsonify({'error': 'Failed to fetch onboarding data'}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            success = model.update_onboarding_progress(user_id, data)
            
            if success:
                return jsonify({'success': True, 'message': 'Onboarding progress updated'})
            else:
                return jsonify({'error': 'Failed to update onboarding progress'}), 400
                
        except Exception as e:
            logger.error(f"Failed to update onboarding progress: {str(e)}")
            return jsonify({'error': 'Failed to update onboarding progress'}), 500

@app.route('/api/onboarding/sample-data', methods=['POST'])
@login_required
def add_sample_data():
    """Add sample data for new users."""
    try:
        user_id = session['user_id']
        
        success = model.add_sample_data(user_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Sample data added successfully'})
        else:
            return jsonify({'error': 'Failed to add sample data'}), 500
            
    except Exception as e:
        logger.error(f"Failed to add sample data: {str(e)}")
        return jsonify({'error': 'Failed to add sample data'}), 500

@app.route('/reports')
@login_required
def reports():
    """Reports and analytics."""
    # Update onboarding progress
    model.update_onboarding_progress(session['user_id'], {'reports_visited': True})
    return render_template('index.html')

@app.route('/api/chart-data')
@login_required
def chart_data():
    """Get data for charts with enhanced date range support."""
    try:
        user_id = session['user_id']
        chart_type = request.args.get('type', 'all')
        
        # Get date range parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        period = request.args.get('period', 'this_month')  # this_month, last_month, custom
        
        # Set default date range based on period
        if not start_date or not end_date:
            current_date = datetime.now()
            
            if period == 'this_month':
                start_date = current_date.replace(day=1).strftime('%Y-%m-%d')
                end_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                end_date = end_date.strftime('%Y-%m-%d')
            elif period == 'last_month':
                last_month = current_date.replace(day=1) - timedelta(days=1)
                start_date = last_month.replace(day=1).strftime('%Y-%m-%d')
                end_date = last_month.strftime('%Y-%m-%d')
            else:  # Default to current month
                start_date = current_date.replace(day=1).strftime('%Y-%m-%d')
                end_date = current_date.strftime('%Y-%m-%d')
        
        data = {}
        
        if chart_type in ['all', 'expense_breakdown']:
            # Expense breakdown by category with date range
            breakdown = model.get_category_breakdown(user_id, start_date, end_date)
            expense_breakdown = []
            for item in breakdown:
                if item['category_type'] == 'expense' and item['total_amount'] > 0:
                    expense_breakdown.append({
                        'category': item['category_name'],
                        'amount': item['total_amount'],
                        'icon': item.get('category_icon', '💸'),
                        'color': item.get('category_color', '#4F8A8B')
                    })
            data['expense_breakdown'] = expense_breakdown
        
        if chart_type in ['all', 'monthly_trends']:
            # Monthly income vs expense trends
            trends = model.get_income_expense_trends(user_id, 6)
            monthly_data = {}
            
            for trend in trends:
                month = trend['month']
                if month not in monthly_data:
                    monthly_data[month] = {'income': 0, 'expense': 0}
                monthly_data[month][trend['type']] = trend['total']
            
            # Convert to arrays for Chart.js
            months = sorted(monthly_data.keys())
            income_data = [monthly_data[month]['income'] for month in months]
            expense_data = [monthly_data[month]['expense'] for month in months]
            
            data['monthly_trends'] = {
                'months': months,
                'income': income_data,
                'expenses': expense_data
            }
        
        if chart_type in ['all', 'dashboard_stats']:
            # Dashboard statistics
            current_date = datetime.now()
            current_month_summary = model.get_monthly_summary(
                user_id, current_date.year, current_date.month
            )
            
            # Previous month
            prev_month = current_date.month - 1 if current_date.month > 1 else 12
            prev_year = current_date.year if current_date.month > 1 else current_date.year - 1
            prev_month_summary = model.get_monthly_summary(user_id, prev_year, prev_month)
            
            data['dashboard_stats'] = {
                'current_month': current_month_summary,
                'previous_month': prev_month_summary
            }
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Failed to fetch chart data: {str(e)}")
        return jsonify({'error': 'Failed to fetch chart data'}), 500

@app.route('/api/categories')
@login_required
def get_categories():
    """Get all categories with enhanced data."""
    try:
        category_type = request.args.get('type')
        categories = model.get_categories(category_type)
        
        category_list = []
        for category in categories:
            category_list.append({
                'id': category['id'],
                'name': category['name'],
                'type': category['type'],
                'icon': category.get('icon', '💳'),
                'color': category.get('color', '#4F8A8B')
            })
        
        return jsonify({'categories': category_list})
        
    except Exception as e:
        logger.error(f"Failed to fetch categories: {str(e)}")
        return jsonify({'error': 'Failed to fetch categories'}), 500

@app.route('/api/transaction/<int:transaction_id>')
@login_required
def get_transaction(transaction_id):
    """Get a specific transaction."""
    try:
        user_id = session['user_id']
        transaction = model.get_transaction_by_id(transaction_id, user_id)
        
        if transaction:
            return jsonify({
                'transaction': {
                    'id': transaction['id'],
                    'amount': transaction['amount'],
                    'type': transaction['type'],
                    'description': transaction['description'],
                    'date': transaction['date'],
                    'category_id': transaction['category_id'],
                    'category_name': transaction['category_name']
                }
            })
        else:
            return jsonify({'error': 'Transaction not found'}), 404
            
    except Exception as e:
        logger.error(f"Failed to fetch transaction: {str(e)}")
        return jsonify({'error': 'Failed to fetch transaction'}), 500

# Settings page
@app.route('/settings')
@login_required
def settings():
    """User settings page."""
    model.update_onboarding_progress(session['user_id'], {'settings_visited': True})
    return render_template('index.html')

# Update the main execution block for Render:
if __name__ == '__main__':
    # Get port from environment (Render sets this)
    port = int(os.environ.get('PORT', 5000))
    
    # Render handles production/development detection
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Finance Manager Pro on port {port}")
    
    app.run(
        host='0.0.0.0',  # Required for Render
        port=port,
        debug=debug,
        threaded=True
    )
