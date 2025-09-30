#!/usr/bin/env python3
"""
Personal Finance Manager Pro - Database Model
=============================================

Complete database operations supporting both PostgreSQL (Render) and SQLite (local).
Handles users, transactions, budgets, categories, and analytics.

Version: 1.0.0
"""

import sqlite3
import logging
import csv
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from io import StringIO
import os
import secrets
from decimal import Decimal

# PostgreSQL support for Render deployment
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2 import sql
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'data/finance.db')

def get_db_connection():
    """
    Get database connection - PostgreSQL for Render, SQLite for local development
    
    Returns:
        Database connection with appropriate row factory
    """
    try:
        if DATABASE_URL and DATABASE_URL.startswith('postgresql') and POSTGRES_AVAILABLE:
            logger.info("Connecting to PostgreSQL database")
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            conn.autocommit = False
            return conn
        else:
            logger.info("Connecting to SQLite database")
            os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
            conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA foreign_keys = ON')
            conn.execute('PRAGMA journal_mode = WAL')
            return conn
            
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def is_postgres():
    """Check if we're using PostgreSQL"""
    return DATABASE_URL and DATABASE_URL.startswith('postgresql') and POSTGRES_AVAILABLE

def get_placeholder():
    """Get parameter placeholder for current database"""
    return '%s' if is_postgres() else '?'

def init_db():
    """Initialize database with all required tables and indexes"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if is_postgres():
            logger.info("Creating PostgreSQL tables")
            _create_postgres_tables(cursor)
        else:
            logger.info("Creating SQLite tables")
            _create_sqlite_tables(cursor)
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise
    finally:
        conn.close()

def _create_postgres_tables(cursor):
    """Create PostgreSQL tables with appropriate data types and constraints"""
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            onboarding_completed BOOLEAN DEFAULT FALSE,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP
        )
    """)
    
    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            type VARCHAR(10) NOT NULL CHECK(type IN ('income', 'expense')),
            icon VARCHAR(10) DEFAULT '💳',
            color VARCHAR(20) DEFAULT '#4F8A8B',
            is_default BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            category_id INTEGER NOT NULL REFERENCES categories(id),
            amount DECIMAL(12,2) NOT NULL CHECK(amount > 0),
            type VARCHAR(10) NOT NULL CHECK(type IN ('income', 'expense')),
            description TEXT,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_recurring BOOLEAN DEFAULT FALSE,
            tags TEXT
        )
    """)
    
    # Budgets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            category_id INTEGER NOT NULL REFERENCES categories(id),
            amount DECIMAL(12,2) NOT NULL CHECK(amount > 0),
            period VARCHAR(20) DEFAULT 'monthly' CHECK(period IN ('weekly', 'monthly', 'yearly')),
            start_date DATE NOT NULL,
            end_date DATE,
            is_active BOOLEAN DEFAULT TRUE,
            alert_threshold DECIMAL(3,2) DEFAULT 0.8,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, category_id, period)
        )
    """)
    
    # User preferences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            currency VARCHAR(10) DEFAULT 'USD',
            currency_symbol VARCHAR(10) DEFAULT '$',
            date_format VARCHAR(20) DEFAULT 'MM/DD/YYYY',
            theme VARCHAR(10) DEFAULT 'auto' CHECK(theme IN ('light', 'dark', 'auto')),
            default_view VARCHAR(20) DEFAULT 'all' CHECK(default_view IN ('all', 'income', 'expense')),
            timezone VARCHAR(50) DEFAULT 'UTC',
            language VARCHAR(10) DEFAULT 'en',
            notifications_enabled BOOLEAN DEFAULT TRUE,
            email_notifications BOOLEAN DEFAULT FALSE,
            budget_alerts BOOLEAN DEFAULT TRUE,
            export_format VARCHAR(10) DEFAULT 'csv',
            decimal_places INTEGER DEFAULT 2,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # User onboarding table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_onboarding (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            tour_completed BOOLEAN DEFAULT FALSE,
            sample_data_added BOOLEAN DEFAULT FALSE,
            first_transaction_added BOOLEAN DEFAULT FALSE,
            first_budget_set BOOLEAN DEFAULT FALSE,
            dashboard_visited BOOLEAN DEFAULT FALSE,
            reports_visited BOOLEAN DEFAULT FALSE,
            settings_visited BOOLEAN DEFAULT FALSE,
            export_used BOOLEAN DEFAULT FALSE,
            search_used BOOLEAN DEFAULT FALSE,
            checklist_completed BOOLEAN DEFAULT FALSE,
            completion_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes
    _create_postgres_indexes(cursor)

def _create_sqlite_tables(cursor):
    """Create SQLite tables with appropriate data types and constraints"""
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            onboarding_completed BOOLEAN DEFAULT FALSE,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP
        )
    """)
    
    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            icon TEXT DEFAULT '💳',
            color TEXT DEFAULT '#4F8A8B',
            is_default BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            category_id INTEGER NOT NULL REFERENCES categories(id),
            amount DECIMAL(12,2) NOT NULL CHECK(amount > 0),
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            description TEXT,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_recurring BOOLEAN DEFAULT FALSE,
            tags TEXT
        )
    """)
    
    # Budgets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            category_id INTEGER NOT NULL REFERENCES categories(id),
            amount DECIMAL(12,2) NOT NULL CHECK(amount > 0),
            period TEXT DEFAULT 'monthly' CHECK(period IN ('weekly', 'monthly', 'yearly')),
            start_date DATE NOT NULL,
            end_date DATE,
            is_active BOOLEAN DEFAULT TRUE,
            alert_threshold DECIMAL(3,2) DEFAULT 0.8,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, category_id, period)
        )
    """)
    
    # User preferences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            currency TEXT DEFAULT 'USD',
            currency_symbol TEXT DEFAULT '$',
            date_format TEXT DEFAULT 'MM/DD/YYYY',
            theme TEXT DEFAULT 'auto' CHECK(theme IN ('light', 'dark', 'auto')),
            default_view TEXT DEFAULT 'all' CHECK(default_view IN ('all', 'income', 'expense')),
            timezone TEXT DEFAULT 'UTC',
            language TEXT DEFAULT 'en',
            notifications_enabled BOOLEAN DEFAULT TRUE,
            email_notifications BOOLEAN DEFAULT FALSE,
            budget_alerts BOOLEAN DEFAULT TRUE,
            export_format TEXT DEFAULT 'csv',
            decimal_places INTEGER DEFAULT 2,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # User onboarding table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_onboarding (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            tour_completed BOOLEAN DEFAULT FALSE,
            sample_data_added BOOLEAN DEFAULT FALSE,
            first_transaction_added BOOLEAN DEFAULT FALSE,
            first_budget_set BOOLEAN DEFAULT FALSE,
            dashboard_visited BOOLEAN DEFAULT FALSE,
            reports_visited BOOLEAN DEFAULT FALSE,
            settings_visited BOOLEAN DEFAULT FALSE,
            export_used BOOLEAN DEFAULT FALSE,
            search_used BOOLEAN DEFAULT FALSE,
            checklist_completed BOOLEAN DEFAULT FALSE,
            completion_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes
    _create_sqlite_indexes(cursor)

def _create_postgres_indexes(cursor):
    """Create PostgreSQL indexes for performance"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date DESC)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_user_type ON transactions(user_id, type)",
        "CREATE INDEX IF NOT EXISTS idx_budgets_user_category ON budgets(user_id, category_id)",
        "CREATE INDEX IF NOT EXISTS idx_budgets_user_active ON budgets(user_id, is_active)",
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_categories_type ON categories(type)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)

def _create_sqlite_indexes(cursor):
    """Create SQLite indexes for performance"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date DESC)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_user_type ON transactions(user_id, type)",
        "CREATE INDEX IF NOT EXISTS idx_budgets_user_category ON budgets(user_id, category_id)",
        "CREATE INDEX IF NOT EXISTS idx_budgets_user_active ON budgets(user_id, is_active)",
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_categories_type ON categories(type)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)

# User Management Functions
def create_user(username: str, email: str, password_hash: str) -> Optional[int]:
    """Create a new user with default preferences and onboarding record"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        if is_postgres():
            cursor.execute(f"""
                INSERT INTO users (username, email, password_hash) 
                VALUES ({placeholder}, {placeholder}, {placeholder}) RETURNING id
            """, (username, email, password_hash))
            user_id = cursor.fetchone()['id']
            
            cursor.execute(f"""
                INSERT INTO user_preferences (user_id) VALUES ({placeholder})
            """, (user_id,))
            
            cursor.execute(f"""
                INSERT INTO user_onboarding (user_id) VALUES ({placeholder})
            """, (user_id,))
        else:
            cursor.execute(f"""
                INSERT INTO users (username, email, password_hash) VALUES ({placeholder}, {placeholder}, {placeholder})
            """, (username, email, password_hash))
            user_id = cursor.lastrowid
            
            cursor.execute(f"""
                INSERT INTO user_preferences (user_id) VALUES ({placeholder})
            """, (user_id,))
            
            cursor.execute(f"""
                INSERT INTO user_onboarding (user_id) VALUES ({placeholder})
            """, (user_id,))
        
        conn.commit()
        logger.info(f"User created successfully: {username} (ID: {user_id})")
        return user_id
        
    except Exception as e:
        logger.error(f"User creation error: {e}")
        return None
    finally:
        conn.close()

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        cursor.execute(f"""
            SELECT id, username, email, password_hash, created_at, last_login, is_active, 
                   failed_login_attempts, locked_until
            FROM users 
            WHERE username = {placeholder} AND is_active = TRUE
        """, (username,))
        
        result = cursor.fetchone()
        return dict(result) if result else None
        
    except Exception as e:
        logger.error(f"Get user error: {e}")
        return None
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        cursor.execute(f"""
            SELECT id, username, email, password_hash, created_at, last_login, is_active
            FROM users 
            WHERE email = {placeholder} AND is_active = TRUE
        """, (email,))
        
        result = cursor.fetchone()
        return dict(result) if result else None
        
    except Exception as e:
        logger.error(f"Get user by email error: {e}")
        return None
    finally:
        conn.close()

def update_user_login(user_id: int) -> bool:
    """Update user's last login timestamp and reset failed attempts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        cursor.execute(f"""
            UPDATE users 
            SET last_login = CURRENT_TIMESTAMP, 
                failed_login_attempts = 0,
                locked_until = NULL
            WHERE id = {placeholder}
        """, (user_id,))
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Update user login error: {e}")
        return False
    finally:
        conn.close()

def increment_failed_login_attempts(username: str) -> bool:
    """Increment failed login attempts and lock account if necessary"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        # Get current attempts
        cursor.execute(f"""
            SELECT failed_login_attempts FROM users WHERE username = {placeholder}
        """, (username,))
        
        result = cursor.fetchone()
        if not result:
            return False
            
        attempts = result[0] + 1
        
        # Lock account for 15 minutes after 5 failed attempts
        if attempts >= 5:
            if is_postgres():
                cursor.execute(f"""
                    UPDATE users 
                    SET failed_login_attempts = {placeholder}, 
                        locked_until = CURRENT_TIMESTAMP + INTERVAL '15 minutes'
                    WHERE username = {placeholder}
                """, (attempts, username))
            else:
                cursor.execute(f"""
                    UPDATE users 
                    SET failed_login_attempts = {placeholder}, 
                        locked_until = datetime('now', '+15 minutes')
                    WHERE username = {placeholder}
                """, (attempts, username))
        else:
            cursor.execute(f"""
                UPDATE users 
                SET failed_login_attempts = {placeholder}
                WHERE username = {placeholder}
            """, (attempts, username))
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Increment failed login attempts error: {e}")
        return False
    finally:
        conn.close()

# Category Management Functions
def seed_default_categories():
    """Seed database with default income and expense categories"""
    default_categories = [
        # Income categories
        ('Salary', 'income', '💰', '#38B27B'),
        ('Freelance', 'income', '💼', '#4CAF50'),
        ('Investment', 'income', '📈', '#2196F3'),
        ('Gift', 'income', '🎁', '#FF9800'),
        ('Other Income', 'income', '💵', '#607D8B'),
        
        # Expense categories
        ('Food & Dining', 'expense', '🍕', '#FF5722'),
        ('Transportation', 'expense', '🚗', '#9C27B0'),
        ('Shopping', 'expense', '🛍️', '#E91E63'),
        ('Entertainment', 'expense', '🎬', '#3F51B5'),
        ('Bills & Utilities', 'expense', '⚡', '#FF9800'),
        ('Healthcare', 'expense', '🏥', '#F44336'),
        ('Education', 'expense', '📚', '#009688'),
        ('Travel', 'expense', '✈️', '#00BCD4'),
        ('Home & Garden', 'expense', '🏠', '#8BC34A'),
        ('Personal Care', 'expense', '💄', '#FFEB3B'),
        ('Insurance', 'expense', '🛡️', '#795548'),
        ('Taxes', 'expense', '📊', '#607D8B'),
        ('Other Expense', 'expense', '💸', '#9E9E9E')
    ]
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        for name, cat_type, icon, color in default_categories:
            try:
                cursor.execute(f"""
                    INSERT INTO categories (name, type, icon, color) 
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                """, (name, cat_type, icon, color))
            except Exception:
                # Category already exists, skip
                pass
        
        conn.commit()
        logger.info("Default categories seeded successfully")
        
    except Exception as e:
        logger.error(f"Seed categories error: {e}")
    finally:
        conn.close()

def get_categories(category_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all categories, optionally filtered by type"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        if category_type:
            cursor.execute(f"""
                SELECT id, name, type, icon, color, is_default, created_at
                FROM categories 
                WHERE type = {placeholder}
                ORDER BY name
            """, (category_type,))
        else:
            cursor.execute("""
                SELECT id, name, type, icon, color, is_default, created_at
                FROM categories 
                ORDER BY type, name
            """)
        
        return [dict(row) for row in cursor.fetchall()]
        
    except Exception as e:
        logger.error(f"Get categories error: {e}")
        return []
    finally:
        conn.close()

def get_category_by_id(category_id: int) -> Optional[Dict[str, Any]]:
    """Get category by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        cursor.execute(f"""
            SELECT id, name, type, icon, color, is_default, created_at
            FROM categories 
            WHERE id = {placeholder}
        """, (category_id,))
        
        result = cursor.fetchone()
        return dict(result) if result else None
        
    except Exception as e:
        logger.error(f"Get category by ID error: {e}")
        return None
    finally:
        conn.close()

# Transaction Management Functions
def create_transaction(user_id: int, transaction_type: str, amount: float, 
                      category_id: int, date: str, description: Optional[str] = None) -> Optional[int]:
    """Create a new transaction"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        if is_postgres():
            cursor.execute(f"""
                INSERT INTO transactions (user_id, category_id, amount, type, description, date) 
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}) 
                RETURNING id
            """, (user_id, category_id, amount, transaction_type, description, date))
            
            transaction_id = cursor.fetchone()['id']
        else:
            cursor.execute(f"""
                INSERT INTO transactions (user_id, category_id, amount, type, description, date) 
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (user_id, category_id, amount, transaction_type, description, date))
            
            transaction_id = cursor.lastrowid
        
        conn.commit()
        logger.info(f"Transaction created successfully: ID {transaction_id}")
        return transaction_id
        
    except Exception as e:
        logger.error(f"Create transaction error: {e}")
        return None
    finally:
        conn.close()

def get_transactions(user_id: int, limit: int = 50, offset: int = 0, 
                    filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Get user transactions with optional filtering"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        # Base query
        query = f"""
            SELECT t.id, t.user_id, t.category_id, t.amount, t.type, t.description, 
                   t.date, t.created_at, t.updated_at,
                   c.name as category_name, c.icon as category_icon, c.color as category_color
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = {placeholder}
        """
        
        params = [user_id]
        
        # Apply filters
        if filters:
            if filters.get('type') and filters['type'] != 'all':
                query += f" AND t.type = {placeholder}"
                params.append(filters['type'])
            
            if filters.get('category_id'):
                query += f" AND t.category_id = {placeholder}"
                params.append(filters['category_id'])
            
            if filters.get('start_date'):
                query += f" AND t.date >= {placeholder}"
                params.append(filters['start_date'])
            
            if filters.get('end_date'):
                query += f" AND t.date <= {placeholder}"
                params.append(filters['end_date'])
            
            if filters.get('search'):
                query += f" AND (t.description ILIKE {placeholder} OR c.name ILIKE {placeholder})" if is_postgres() else f" AND (t.description LIKE {placeholder} OR c.name LIKE {placeholder})"
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term])
        
        # Apply sorting
        sort_by = filters.get('sort_by', 'date_desc') if filters else 'date_desc'
        if sort_by == 'date_asc':
            query += " ORDER BY t.date ASC"
        elif sort_by == 'amount_desc':
            query += " ORDER BY t.amount DESC"
        elif sort_by == 'amount_asc':
            query += " ORDER BY t.amount ASC"
        else:  # date_desc
            query += " ORDER BY t.date DESC"
        
        # Apply pagination
        query += f" LIMIT {placeholder} OFFSET {placeholder}"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
        
    except Exception as e:
        logger.error(f"Get transactions error: {e}")
        return []
    finally:
        conn.close()

def get_transaction_by_id(user_id: int, transaction_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific transaction by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        cursor.execute(f"""
            SELECT t.id, t.user_id, t.category_id, t.amount, t.type, t.description, 
                   t.date, t.created_at, t.updated_at,
                   c.name as category_name, c.icon as category_icon, c.color as category_color
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.id = {placeholder} AND t.user_id = {placeholder}
        """, (transaction_id, user_id))
        
        result = cursor.fetchone()
        return dict(result) if result else None
        
    except Exception as e:
        logger.error(f"Get transaction by ID error: {e}")
        return None
    finally:
        conn.close()

def update_transaction(user_id: int, transaction_id: int, **kwargs) -> bool:
    """Update a transaction"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        # Build update query dynamically
        valid_fields = ['amount', 'type', 'category_id', 'description', 'date']
        updates = []
        params = []
        
        for field, value in kwargs.items():
            if field in valid_fields and value is not None:
                updates.append(f"{field} = {placeholder}")
                params.append(value)
        
        if not updates:
            return False
        
        # Add updated_at timestamp
        updates.append(f"updated_at = CURRENT_TIMESTAMP")
        
        # Add WHERE conditions
        params.extend([transaction_id, user_id])
        
        query = f"""
            UPDATE transactions 
            SET {', '.join(updates)}
            WHERE id = {placeholder} AND user_id = {placeholder}
        """
        
        cursor.execute(query, params)
        conn.commit()
        
        return cursor.rowcount > 0
        
    except Exception as e:
        logger.error(f"Update transaction error: {e}")
        return False
    finally:
        conn.close()

def delete_transaction(user_id: int, transaction_id: int) -> bool:
    """Delete a transaction"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        cursor.execute(f"""
            DELETE FROM transactions 
            WHERE id = {placeholder} AND user_id = {placeholder}
        """, (transaction_id, user_id))
        
        conn.commit()
        return cursor.rowcount > 0
        
    except Exception as e:
        logger.error(f"Delete transaction error: {e}")
        return False
    finally:
        conn.close()

def get_transaction_summary(user_id: int, start_date: Optional[str] = None, 
                          end_date: Optional[str] = None) -> Dict[str, Any]:
    """Get transaction summary for a user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        # Base query conditions
        where_conditions = [f"user_id = {placeholder}"]
        params = [user_id]
        
        if start_date:
            where_conditions.append(f"date >= {placeholder}")
            params.append(start_date)
        
        if end_date:
            where_conditions.append(f"date <= {placeholder}")
            params.append(end_date)
        
        where_clause = " AND ".join(where_conditions)
        
        # Get summary data
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_count,
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as total_income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as total_expense,
                COUNT(CASE WHEN type = 'income' THEN 1 END) as income_count,
                COUNT(CASE WHEN type = 'expense' THEN 1 END) as expense_count
            FROM transactions 
            WHERE {where_clause}
        """, params)
        
        result = cursor.fetchone()
        
        if result:
            summary = dict(result)
            summary['net_balance'] = float(summary['total_income']) - float(summary['total_expense'])
            summary['savings_rate'] = (summary['net_balance'] / float(summary['total_income']) * 100) if summary['total_income'] > 0 else 0
            return summary
        
        return {
            'total_count': 0,
            'total_income': 0,
            'total_expense': 0,
            'income_count': 0,
            'expense_count': 0,
            'net_balance': 0,
            'savings_rate': 0
        }
        
    except Exception as e:
        logger.error(f"Get transaction summary error: {e}")
        return {}
    finally:
        conn.close()

# Budget Management Functions
def create_budget(user_id: int, category_id: int, amount: float, 
                 period: str = 'monthly', start_date: str = None) -> Optional[int]:
    """Create a new budget"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        
        if is_postgres():
            cursor.execute(f"""
                INSERT INTO budgets (user_id, category_id, amount, period, start_date) 
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}) 
                RETURNING id
            """, (user_id, category_id, amount, period, start_date))
            
            budget_id = cursor.fetchone()['id']
        else:
            cursor.execute(f"""
                INSERT INTO budgets (user_id, category_id, amount, period, start_date) 
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (user_id, category_id, amount, period, start_date))
            
            budget_id = cursor.lastrowid
        
        conn.commit()
        logger.info(f"Budget created successfully: ID {budget_id}")
        return budget_id
        
    except Exception as e:
        logger.error(f"Create budget error: {e}")
        return None
    finally:
        conn.close()

def get_budgets(user_id: int, is_active: bool = True) -> List[Dict[str, Any]]:
    """Get user budgets with spending information"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        # Get current date for period calculations
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute(f"""
            SELECT b.id, b.user_id, b.category_id, b.amount as budget_amount, 
                   b.period, b.start_date, b.end_date, b.is_active, b.alert_threshold,
                   b.created_at, b.updated_at,
                   c.name as category_name, c.icon as category_icon, c.color as category_color,
                   COALESCE(SUM(t.amount), 0) as actual_spent
            FROM budgets b
            JOIN categories c ON b.category_id = c.id
            LEFT JOIN transactions t ON (
                t.user_id = b.user_id 
                AND t.category_id = b.category_id 
                AND t.type = 'expense'
                AND t.date >= b.start_date
                AND (b.end_date IS NULL OR t.date <= b.end_date)
            )
            WHERE b.user_id = {placeholder} AND b.is_active = {placeholder}
            GROUP BY b.id, b.user_id, b.category_id, b.amount, b.period, b.start_date, 
                     b.end_date, b.is_active, b.alert_threshold, b.created_at, b.updated_at,
                     c.name, c.icon, c.color
            ORDER BY b.created_at DESC
        """, (user_id, is_active))
        
        return [dict(row) for row in cursor.fetchall()]
        
    except Exception as e:
        logger.error(f"Get budgets error: {e}")
        return []
    finally:
        conn.close()

def delete_budget(user_id: int, budget_id: int) -> bool:
    """Delete a budget"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        cursor.execute(f"""
            DELETE FROM budgets 
            WHERE id = {placeholder} AND user_id = {placeholder}
        """, (budget_id, user_id))
        
        conn.commit()
        return cursor.rowcount > 0
        
    except Exception as e:
        logger.error(f"Delete budget error: {e}")
        return False
    finally:
        conn.close()

# Analytics and Insights Functions
def get_monthly_trends(user_id: int, months: int = 6) -> Dict[str, Any]:
    """Get monthly income and expense trends"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        # Calculate start date
        start_date = (datetime.now() - timedelta(days=months * 30)).strftime('%Y-%m-%d')
        
        if is_postgres():
            cursor.execute(f"""
                SELECT 
                    TO_CHAR(date, 'YYYY-MM') as month,
                    SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
                FROM transactions 
                WHERE user_id = {placeholder} AND date >= {placeholder}
                GROUP BY TO_CHAR(date, 'YYYY-MM')
                ORDER BY month
            """, (user_id, start_date))
        else:
            cursor.execute(f"""
                SELECT 
                    strftime('%Y-%m', date) as month,
                    SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
                FROM transactions 
                WHERE user_id = {placeholder} AND date >= {placeholder}
                GROUP BY strftime('%Y-%m', date)
                ORDER BY month
            """, (user_id, start_date))
        
        results = cursor.fetchall()
        
        return {
            'months': [row[0] for row in results],
            'income': [float(row[1]) for row in results],
            'expenses': [float(row[2]) for row in results]
        }
        
    except Exception as e:
        logger.error(f"Get monthly trends error: {e}")
        return {'months': [], 'income': [], 'expenses': []}
    finally:
        conn.close()

def get_category_breakdown(user_id: int, transaction_type: str = 'expense', 
                          start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get spending breakdown by category"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        # Build query conditions
        where_conditions = [f"t.user_id = {placeholder}", f"t.type = {placeholder}"]
        params = [user_id, transaction_type]
        
        if start_date:
            where_conditions.append(f"t.date >= {placeholder}")
            params.append(start_date)
        
        if end_date:
            where_conditions.append(f"t.date <= {placeholder}")
            params.append(end_date)
        
        where_clause = " AND ".join(where_conditions)
        
        cursor.execute(f"""
            SELECT 
                c.name as category,
                c.icon,
                c.color,
                SUM(t.amount) as amount,
                COUNT(t.id) as transaction_count
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE {where_clause}
            GROUP BY c.id, c.name, c.icon, c.color
            ORDER BY amount DESC
        """, params)
        
        return [dict(row) for row in cursor.fetchall()]
        
    except Exception as e:
        logger.error(f"Get category breakdown error: {e}")
        return []
    finally:
        conn.close()

def search_transactions(user_id: int, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Search transactions by description or category name"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        search_term = f"%{query}%"
        
        if is_postgres():
            cursor.execute(f"""
                SELECT t.id, t.amount, t.type, t.description, t.date,
                       c.name as category_name, c.icon as category_icon, c.color as category_color
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = {placeholder} 
                AND (t.description ILIKE {placeholder} OR c.name ILIKE {placeholder})
                ORDER BY t.date DESC
                LIMIT {placeholder}
            """, (user_id, search_term, search_term, limit))
        else:
            cursor.execute(f"""
                SELECT t.id, t.amount, t.type, t.description, t.date,
                       c.name as category_name, c.icon as category_icon, c.color as category_color
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = {placeholder} 
                AND (t.description LIKE {placeholder} OR c.name LIKE {placeholder})
                ORDER BY t.date DESC
                LIMIT {placeholder}
            """, (user_id, search_term, search_term, limit))
        
        return [dict(row) for row in cursor.fetchall()]
        
    except Exception as e:
        logger.error(f"Search transactions error: {e}")
        return []
    finally:
        conn.close()

# User Preferences Functions
def get_user_preferences(user_id: int) -> Dict[str, Any]:
    """Get user preferences"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        cursor.execute(f"""
            SELECT currency, currency_symbol, date_format, theme, default_view,
                   timezone, language, notifications_enabled, email_notifications,
                   budget_alerts, export_format, decimal_places
            FROM user_preferences 
            WHERE user_id = {placeholder}
        """, (user_id,))
        
        result = cursor.fetchone()
        return dict(result) if result else {}
        
    except Exception as e:
        logger.error(f"Get user preferences error: {e}")
        return {}
    finally:
        conn.close()

def update_user_preferences(user_id: int, preferences: Dict[str, Any]) -> bool:
    """Update user preferences"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        # Build update query
        valid_fields = [
            'currency', 'currency_symbol', 'date_format', 'theme', 'default_view',
            'timezone', 'language', 'notifications_enabled', 'email_notifications',
            'budget_alerts', 'export_format', 'decimal_places'
        ]
        
        updates = []
        params = []
        
        for field, value in preferences.items():
            if field in valid_fields and value is not None:
                updates.append(f"{field} = {placeholder}")
                params.append(value)
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(user_id)
        
        query = f"""
            UPDATE user_preferences 
            SET {', '.join(updates)}
            WHERE user_id = {placeholder}
        """
        
        cursor.execute(query, params)
        conn.commit()
        
        return cursor.rowcount > 0
        
    except Exception as e:
        logger.error(f"Update user preferences error: {e}")
        return False
    finally:
        conn.close()

# Onboarding Functions
def get_user_onboarding(user_id: int) -> Dict[str, Any]:
    """Get user onboarding status"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        cursor.execute(f"""
            SELECT tour_completed, sample_data_added, first_transaction_added,
                   first_budget_set, dashboard_visited, reports_visited,
                   settings_visited, export_used, search_used, checklist_completed,
                   completion_date
            FROM user_onboarding 
            WHERE user_id = {placeholder}
        """, (user_id,))
        
        result = cursor.fetchone()
        return dict(result) if result else {}
        
    except Exception as e:
        logger.error(f"Get user onboarding error: {e}")
        return {}
    finally:
        conn.close()

def update_user_onboarding(user_id: int, updates: Dict[str, Any]) -> bool:
    """Update user onboarding progress"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        valid_fields = [
            'tour_completed', 'sample_data_added', 'first_transaction_added',
            'first_budget_set', 'dashboard_visited', 'reports_visited',
            'settings_visited', 'export_used', 'search_used', 'checklist_completed'
        ]
        
        update_fields = []
        params = []
        
        for field, value in updates.items():
            if field in valid_fields and value is not None:
                update_fields.append(f"{field} = {placeholder}")
                params.append(value)
        
        if not update_fields:
            return False
        
        # Check if checklist is completed
        if updates.get('checklist_completed'):
            update_fields.append("completion_date = CURRENT_TIMESTAMP")
        
        params.append(user_id)
        
        query = f"""
            UPDATE user_onboarding 
            SET {', '.join(update_fields)}
            WHERE user_id = {placeholder}
        """
        
        cursor.execute(query, params)
        conn.commit()
        
        return cursor.rowcount > 0
        
    except Exception as e:
        logger.error(f"Update user onboarding error: {e}")
        return False
    finally:
        conn.close()

# Export Functions
def export_transactions_csv(user_id: int, start_date: Optional[str] = None, 
                           end_date: Optional[str] = None) -> str:
    """Export user transactions as CSV"""
    try:
        # Get transactions
        filters = {}
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        
        transactions = get_transactions(user_id, limit=10000, filters=filters)
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Date', 'Category', 'Type', 'Description', 'Amount'
        ])
        
        # Write transactions
        for transaction in transactions:
            writer.writerow([
                transaction['date'],
                transaction['category_name'],
                transaction['type'].title(),
                transaction['description'] or '',
                f"{transaction['amount']:.2f}"
            ])
        
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Export transactions CSV error: {e}")
        return ""

# Database utilities
def get_database_stats() -> Dict[str, int]:
    """Get database statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Count records in each table
        tables = ['users', 'transactions', 'categories', 'budgets']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        
        return stats
        
    except Exception as e:
        logger.error(f"Get database stats error: {e}")
        return {}
    finally:
        conn.close()

def vacuum_database():
    """Optimize database (SQLite only)"""
    if is_postgres():
        logger.info("VACUUM not needed for PostgreSQL")
        return
    
    try:
        conn = get_db_connection()
        conn.execute("VACUUM")
        conn.close()
        logger.info("Database vacuumed successfully")
        
    except Exception as e:
        logger.error(f"Database vacuum error: {e}")

# Test database connection
def test_connection() -> bool:
    """Test database connection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()
        logger.info("Database connection test successful")
        return result is not None
        
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Testing database connection and initialization...")
    
    if test_connection():
        logger.info("✅ Database connection successful")
        
        try:
            init_db()
            logger.info("✅ Database initialized successfully")
            
            seed_default_categories()
            logger.info("✅ Default categories seeded")
            
            stats = get_database_stats()
            logger.info(f"✅ Database stats: {stats}")
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
    else:
        logger.error("❌ Database connection failed")
