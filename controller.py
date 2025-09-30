#!/usr/bin/env python3
"""
Personal Finance Manager Pro - Main Application Controller
=========================================================

Complete Flask application with Render deployment optimization.
Supports PostgreSQL (Render) and SQLite (local development).

Version: 1.0.0
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

from flask import Flask, request, jsonify, session, render_template, Response, abort, redirect, url_for
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import RequestEntityTooLarge
import bleach
import html

import model
from config import Config

def setup_logging():
    """Setup logging optimized for Render deployment"""
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Render captures stdout/stderr automatically
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()],
        force=True
    )
    
    logger = logging.getLogger(__name__)
    
    # Suppress noisy logs in production
    if os.environ.get('FLASK_ENV') == 'production':
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger.info("Logging configured for Render deployment")
    return logger

# Initialize logging
logger = setup_logging()

# Initialize Flask application
app = Flask(__name__)

# Render-optimized configuration
class RenderConfig(Config):
    """Configuration optimized for Render deployment"""
    PORT = int(os.environ.get('PORT', 5000))
    FORCE_HTTPS = os.environ.get('RENDER_EXTERNAL_URL') is not None
    SESSION_COOKIE_SECURE = bool(os.environ.get('RENDER_EXTERNAL_URL'))
    RATE_LIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')

app.config.from_object(RenderConfig)

# Security configuration
csp = {
    'default-src': "'self'",
    'script-src': [
        "'self'",
        "'unsafe-inline'",
        'cdn.jsdelivr.net',
        'https://fonts.googleapis.com'
    ],
    'style-src': [
        "'self'",
        "'unsafe-inline'",
        'fonts.googleapis.com'
    ],
    'font-src': ["'self'", 'fonts.gstatic.com'],
    'img-src': ["'self'", 'data:', 'blob:'],
    'connect-src': "'self'",
}

# Initialize security
Talisman(app, 
    force_https=app.config['FORCE_HTTPS'],
    strict_transport_security=True,
    content_security_policy=csp,
    feature_policy={'geolocation': "'none'", 'camera': "'none'", 'microphone': "'none'"}
)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["1000 per hour"],
    storage_uri=app.config.get('RATE_LIMIT_STORAGE_URL', 'memory://')
)

# Utility Functions
def sanitize_input(data: Any) -> Any:
    """Sanitize user input to prevent XSS attacks"""
    if isinstance(data, str):
        sanitized = bleach.clean(data, tags=[], strip=True)
        return html.escape(sanitized)
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data

def validate_amount(amount: Any) -> float:
    """Validate and convert amount to float"""
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            raise ValueError("Amount must be positive")
        if amount_float > 1000000:
            raise ValueError("Amount exceeds maximum limit")
        return round(amount_float, 2)
    except (TypeError, ValueError) as e:
        logger.warning(f"Invalid amount provided: {amount}")
        raise ValueError(f"Invalid amount: {str(e)}")

def validate_date(date_str: str) -> str:
    """Validate date format and range"""
    try:
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        max_future_date = date.today() + timedelta(days=30)
        if parsed_date > max_future_date:
            raise ValueError("Date cannot be more than 30 days in the future")
            
        min_past_date = date.today() - timedelta(days=3650)
        if parsed_date < min_past_date:
            raise ValueError("Date cannot be more than 10 years in the past")
            
        return date_str
    except ValueError as e:
        logger.warning(f"Invalid date provided: {date_str}")
        raise ValueError(f"Invalid date: {str(e)}")

# Authentication Decorators
def login_required(f):
    """Require user authentication for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.info(f"Unauthorized access attempt to {request.endpoint}")
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def log_user_action(action: str):
    """Decorator to log user actions"""
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
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Bad request', 'message': 'Invalid request data'}), 400
    return render_template('index.html'), 400

@app.errorhandler(401)
def unauthorized(error):
    logger.warning(f"Unauthorized access: {request.url}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401
    return render_template('index.html'), 401

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
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error', 'message': 'Something went wrong'}), 500
    return render_template('index.html'), 500

# Database initialization flag
_initialized = False

@app.before_request
def initialize_application():
    """Initialize database and application (once)"""
    global _initialized
    if not _initialized:
        try:
            logger.info("Initializing application...")
            model.init_db()
            model.seed_default_categories()
            logger.info("Application initialized successfully")
            _initialized = True
        except Exception as e:
            logger.critical(f"Application initialization failed: {str(e)}")
            raise


# Security Headers
@app.after_request
def after_request(response):
    """Add security headers and handle CORS"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Cache static assets
    if request.endpoint and 'static' in request.endpoint:
        response.headers['Cache-Control'] = 'public, max-age=31536000'
    
    return response

# Main Routes
@app.route('/')
def index():
    """Main application route"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        # Test database connection
        if model.test_connection():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'database': 'connected'
            }), 200
        else:
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'disconnected'
            }), 503
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 503

# Authentication Routes
@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
@log_user_action("login_attempt")
def login():
    """Handle user login"""
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
            # Check if account is locked
            if user.get('locked_until'):
                locked_until = datetime.fromisoformat(str(user['locked_until']))
                if datetime.now() < locked_until:
                    return jsonify({'error': 'Account is temporarily locked'}), 401
            
            # Regenerate session
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session.permanent = True
            
            model.update_user_login(user['id'])
            
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
            # Increment failed attempts
            if user:
                model.increment_failed_login_attempts(username)
            
            logger.warning(f"Failed login attempt for user {username}")
            time.sleep(1)  # Prevent timing attacks
            return jsonify({'error': 'Invalid username or password'}), 401
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/register', methods=['POST'])
@limiter.limit("3 per minute")
@log_user_action("registration_attempt")
def register():
    """Handle user registration"""
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
            session.clear()
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

@app.route('/api/logout', methods=['POST'])
@log_user_action("logout")
def logout():
    """Handle user logout"""
    user_id = session.get('user_id')
    session.clear()
    
    if user_id:
        logger.info(f"User {user_id} logged out")
    
    return jsonify({'success': True, 'message': 'Logged out successfully'})

# Transaction Routes
@app.route('/api/transactions', methods=['GET', 'POST'])
@login_required
@limiter.limit("100 per minute")
def handle_transactions():
    """Handle transaction operations"""
    user_id = session['user_id']
    
    if request.method == 'GET':
        try:
            # Parse filters
            filters = {
                'type': sanitize_input(request.args.get('type', 'all')),
                'category_id': request.args.get('category_id'),
                'start_date': request.args.get('start_date'),
                'end_date': request.args.get('end_date'),
                'sort_by': sanitize_input(request.args.get('sort_by', 'date_desc')),
                'search': sanitize_input(request.args.get('search', ''))
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
            
            # Clean up filters
            filters = {k: v for k, v in filters.items() if v and v != 'all' and v != ''}
            
            # Get pagination parameters
            limit = min(int(request.args.get('limit', 50)), 100)
            offset = int(request.args.get('offset', 0))
            
            transactions = model.get_transactions(user_id, limit=limit, offset=offset, filters=filters)
            summary = model.get_transaction_summary(user_id, filters.get('start_date'), filters.get('end_date'))
            
            return jsonify({
                'transactions': transactions,
                'summary': summary,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'has_more': len(transactions) == limit
                }
            })
            
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
                return jsonify({'error': 'Invalid category for transaction type'}), 400
            
            # Create transaction
            transaction_id = model.create_transaction(
                user_id=user_id,
                transaction_type=transaction_type,
                amount=amount,
                category_id=category_id,
                date=date_str,
                description=description
            )
            
            if transaction_id:
                # Update onboarding progress
                model.update_user_onboarding(user_id, {'first_transaction_added': True})
                
                logger.info(f"Transaction created: ID {transaction_id} for user {user_id}")
                
                return jsonify({
                    'success': True,
                    'message': 'Transaction created successfully',
                    'transaction_id': transaction_id
                })
            else:
                return jsonify({'error': 'Failed to create transaction'}), 500
                
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Transaction creation error: {str(e)}")
            return jsonify({'error': 'Failed to create transaction'}), 500

@app.route('/api/transactions/<int:transaction_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def handle_transaction(transaction_id):
    """Handle individual transaction operations"""
    user_id = session['user_id']
    
    if request.method == 'GET':
        try:
            transaction = model.get_transaction_by_id(user_id, transaction_id)
            if transaction:
                return jsonify({'transaction': transaction})
            else:
                return jsonify({'error': 'Transaction not found'}), 404
                
        except Exception as e:
            logger.error(f"Error fetching transaction {transaction_id}: {str(e)}")
            return jsonify({'error': 'Failed to fetch transaction'}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validate update data
            updates = {}
            if 'amount' in data:
                updates['amount'] = validate_amount(data['amount'])
            if 'type' in data:
                transaction_type = sanitize_input(data['type']).lower()
                if transaction_type not in ['income', 'expense']:
                    return jsonify({'error': 'Invalid transaction type'}), 400
                updates['type'] = transaction_type
            if 'category_id' in data:
                updates['category_id'] = int(data['category_id'])
            if 'description' in data:
                updates['description'] = sanitize_input(data['description'])[:200]
            if 'date' in data:
                updates['date'] = validate_date(data['date'])
            
            success = model.update_transaction(user_id, transaction_id, **updates)
            
            if success:
                return jsonify({'success': True, 'message': 'Transaction updated successfully'})
            else:
                return jsonify({'error': 'Transaction not found or access denied'}), 404
                
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error updating transaction {transaction_id}: {str(e)}")
            return jsonify({'error': 'Failed to update transaction'}), 500
    
    elif request.method == 'DELETE':
        try:
            success = model.delete_transaction(user_id, transaction_id)
            
            if success:
                return jsonify({'success': True, 'message': 'Transaction deleted successfully'})
            else:
                return jsonify({'error': 'Transaction not found or access denied'}), 404
                
        except Exception as e:
            logger.error(f"Error deleting transaction {transaction_id}: {str(e)}")
            return jsonify({'error': 'Failed to delete transaction'}), 500

# Search Routes
@app.route('/api/search/transactions')
@login_required
def search_transactions():
    """Search transactions"""
    try:
        user_id = session['user_id']
        query = request.args.get('q', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({'transactions': [], 'count': 0})
        
        limit = min(int(request.args.get('limit', 20)), 50)
        transactions = model.search_transactions(user_id, query, limit=limit)
        
        # Update onboarding progress
        model.update_user_onboarding(user_id, {'search_used': True})
        
        return jsonify({
            'transactions': transactions,
            'count': len(transactions),
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

# Category Routes
@app.route('/api/categories')
@login_required
def get_categories():
    """Get categories"""
    try:
        category_type = request.args.get('type')
        categories = model.get_categories(category_type)
        return jsonify({'categories': categories})
        
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        return jsonify({'error': 'Failed to fetch categories'}), 500

# Budget Routes
@app.route('/api/budgets', methods=['GET', 'POST'])
@login_required
def handle_budgets():
    """Handle budget operations"""
    user_id = session['user_id']
    
    if request.method == 'GET':
        try:
            budgets = model.get_budgets(user_id)
            return jsonify({'budgets': budgets})
            
        except Exception as e:
            logger.error(f"Error fetching budgets: {str(e)}")
            return jsonify({'error': 'Failed to fetch budgets'}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validate required fields
            required_fields = ['category_id', 'amount', 'period']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'{field} is required'}), 400
            
            amount = validate_amount(data['amount'])
            period = data['period']
            if period not in ['weekly', 'monthly', 'yearly']:
                return jsonify({'error': 'Invalid period'}), 400
            
            budget_id = model.create_budget(
                user_id=user_id,
                category_id=int(data['category_id']),
                amount=amount,
                period=period,
                start_date=data.get('start_date')
            )
            
            if budget_id:
                # Update onboarding progress
                model.update_user_onboarding(user_id, {'first_budget_set': True})
                
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
            logger.error(f"Error creating budget: {str(e)}")
            return jsonify({'error': 'Failed to create budget'}), 500

@app.route('/api/budgets/<int:budget_id>', methods=['DELETE'])
@login_required
def delete_budget(budget_id):
    """Delete a budget"""
    try:
        user_id = session['user_id']
        success = model.delete_budget(user_id, budget_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Budget deleted successfully'})
        else:
            return jsonify({'error': 'Budget not found or access denied'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting budget {budget_id}: {str(e)}")
        return jsonify({'error': 'Failed to delete budget'}), 500

# Analytics Routes
@app.route('/api/chart-data')
@login_required
def get_chart_data():
    """Get chart data for dashboard"""
    try:
        user_id = session['user_id']
        
        # Get parameters
        period = request.args.get('period', 'this_month')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Calculate date range if not provided
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
        
        # Monthly trends
        monthly_trends = model.get_monthly_trends(user_id, months=6)
        data['monthly_trends'] = monthly_trends
        
        # Category breakdown
        expense_breakdown = model.get_category_breakdown(
            user_id, 'expense', start_date, end_date
        )
        data['expense_breakdown'] = expense_breakdown
        
        # Dashboard stats
        current_summary = model.get_transaction_summary(user_id, start_date, end_date)
        data['dashboard_stats'] = {
            'current_month': current_summary
        }
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error fetching chart data: {str(e)}")
        return jsonify({'error': 'Failed to fetch chart data'}), 500

@app.route('/api/insights')
@login_required
def get_insights():
    """Get financial insights"""
    try:
        user_id = session['user_id']
        days = int(request.args.get('days', 30))
        
        # Calculate date range
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Get summary data
        summary = model.get_transaction_summary(user_id, start_date, end_date)
        
        # Get top categories
        top_categories = model.get_category_breakdown(user_id, 'expense', start_date, end_date)[:5]
        
        insights = {
            'total_income': summary.get('total_income', 0),
            'total_expense': summary.get('total_expense', 0),
            'net_balance': summary.get('net_balance', 0),
            'savings_rate': summary.get('savings_rate', 0),
            'avg_daily_spending': summary.get('total_expense', 0) / days if days > 0 else 0,
            'top_categories': top_categories,
            'period_days': days
        }
        
        return jsonify({'insights': insights})
        
    except Exception as e:
        logger.error(f"Error fetching insights: {str(e)}")
        return jsonify({'error': 'Failed to fetch insights'}), 500

# Export Routes
@app.route('/api/export/transactions')
@login_required
def export_transactions():
    """Export transactions to CSV"""
    try:
        user_id = session['user_id']
        
        # Get date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        csv_data = model.export_transactions_csv(user_id, start_date, end_date)
        
        if not csv_data:
            return jsonify({'error': 'No data to export'}), 400
        
        # Update onboarding progress
        model.update_user_onboarding(user_id, {'export_used': True})
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'transactions_{timestamp}.csv'
        
        response = Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting transactions: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500

# User Settings Routes
@app.route('/api/preferences', methods=['GET', 'PUT'])
@login_required
def handle_preferences():
    """Handle user preferences"""
    user_id = session['user_id']
    
    if request.method == 'GET':
        try:
            preferences = model.get_user_preferences(user_id)
            return jsonify({'preferences': preferences})
            
        except Exception as e:
            logger.error(f"Error fetching preferences: {str(e)}")
            return jsonify({'error': 'Failed to fetch preferences'}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            success = model.update_user_preferences(user_id, data)
            
            if success:
                return jsonify({'success': True, 'message': 'Preferences updated successfully'})
            else:
                return jsonify({'error': 'Failed to update preferences'}), 400
                
        except Exception as e:
            logger.error(f"Error updating preferences: {str(e)}")
            return jsonify({'error': 'Failed to update preferences'}), 500

# Onboarding Routes
@app.route('/api/onboarding', methods=['GET', 'PUT'])
@login_required
def handle_onboarding():
    """Handle user onboarding"""
    user_id = session['user_id']
    
    if request.method == 'GET':
        try:
            onboarding = model.get_user_onboarding(user_id)
            return jsonify({'onboarding': onboarding})
            
        except Exception as e:
            logger.error(f"Error fetching onboarding: {str(e)}")
            return jsonify({'error': 'Failed to fetch onboarding'}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            success = model.update_user_onboarding(user_id, data)
            
            if success:
                return jsonify({'success': True, 'message': 'Onboarding updated successfully'})
            else:
                return jsonify({'error': 'Failed to update onboarding'}), 400
                
        except Exception as e:
            logger.error(f"Error updating onboarding: {str(e)}")
            return jsonify({'error': 'Failed to update onboarding'}), 500

# Admin/Debug Routes (only in development)
@app.route('/api/debug/stats')
def debug_stats():
    """Get database statistics (development only)"""
    if os.environ.get('FLASK_ENV') != 'development':
        abort(404)
    
    try:
        stats = model.get_database_stats()
        return jsonify({
            'database_stats': stats,
            'session_user': session.get('user_id'),
            'environment': os.environ.get('FLASK_ENV'),
            'database_type': 'PostgreSQL' if model.is_postgres() else 'SQLite'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Static file serving (for development)
@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files (development only)"""
    return app.send_static_file(filename)

# Catch-all route for SPA
@app.route('/<path:path>')
def catch_all(path):
    """Catch-all route for single page application"""
    return render_template('index.html')

# Application startup
def create_app():
    """Application factory"""
    return app

if __name__ == '__main__':
    # Get configuration from environment
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Personal Finance Manager Pro")
    logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    logger.info(f"Database: {'PostgreSQL' if model.is_postgres() else 'SQLite'}")
    logger.info(f"Port: {port}")
    logger.info(f"Debug: {debug}")
    
    try:
        # Test database connection
        if model.test_connection():
            logger.info("✅ Database connection successful")
        else:
            logger.error("❌ Database connection failed")
            
        # Initialize database
        model.init_db()
        model.seed_default_categories()
        logger.info("✅ Database initialized")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise
    
    # Start the application
    app.run(
        host='0.0.0.0',  # Required for Render
        port=port,
        debug=debug,
        threaded=True
    )
