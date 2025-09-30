#!/usr/bin/env python3
"""
Personal Finance Manager Pro - Database Model
============================================

Comprehensive database operations for personal finance management including:
- User management with preferences and onboarding
- Transaction CRUD with advanced filtering
- Budget tracking and performance monitoring
- Analytics and insights generation
- Data export capabilities
- Security-focused design

Version: 1.0.0
Author: Finance Manager Team
License: MIT
"""

import sqlite3
import logging
import csv
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from io import StringIO
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'data/finance.db')

def get_db_connection():
    """
    Get database connection with row factory for easier access.
    
    Returns:
        sqlite3.Connection: Database connection with row factory
        
    Raises:
        sqlite3.Error: If connection fails
    """
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        # Enable foreign key constraints
        conn.execute('PRAGMA foreign_keys = ON')
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

def init_db():
    """
    Initialize database with all required tables and indexes.
    
    Creates tables for:
    - users: User accounts with security features
    - categories: Transaction categories with icons and colors
    - transactions: Financial transactions with full tracking
    - budgets: Budget management with periods
    - user_preferences: User customization settings
    - user_onboarding: Onboarding progress tracking
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Users table with enhanced security
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
        
        # Categories with visual customization
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
        
        # Transactions with comprehensive tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                description TEXT,
                date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_recurring BOOLEAN DEFAULT FALSE,
                tags TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        # Budgets with flexible periods
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                period TEXT DEFAULT 'monthly' CHECK(period IN ('weekly', 'monthly', 'yearly')),
                start_date DATE NOT NULL,
                end_date DATE,
                is_active BOOLEAN DEFAULT TRUE,
                alert_threshold REAL DEFAULT 0.8,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id),
                UNIQUE(user_id, category_id, period)
            )
        """)
        
        # User preferences for customization
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Onboarding progress tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_onboarding (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Performance indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions(amount)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_user_category ON budgets(user_id, category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_active ON budgets(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        
        # Triggers for automatic timestamp updates
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_transaction_timestamp 
            AFTER UPDATE ON transactions
            BEGIN
                UPDATE transactions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_budget_timestamp 
            AFTER UPDATE ON budgets
            BEGIN
                UPDATE budgets SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        """)
        
        conn.commit()
        logger.info("Database initialized successfully with all tables and indexes")
        
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise
    finally:
        conn.close()

def seed_default_categories():
    """
    Insert default categories with professional icons and colors.
    
    Creates comprehensive categories for both income and expenses
    with modern icons and color coding for better UX.
    """
    default_categories = [
        # Income categories
        ('Salary', 'income', '💰', '#4CAF50'),
        ('Freelance', 'income', '💼', '#2196F3'),
        ('Business', 'income', '🏢', '#FF9800'),
        ('Investments', 'income', '📈', '#9C27B0'),
        ('Rental Income', 'income', '🏠', '#607D8B'),
        ('Side Hustle', 'income', '⚡', '#00BCD4'),
        ('Gifts Received', 'income', '🎁', '#E91E63'),
        ('Other Income', 'income', '💵', '#795548'),
        
        # Expense categories
        ('Food & Dining', 'expense', '🍽️', '#F44336'),
        ('Transportation', 'expense', '🚗', '#3F51B5'),
        ('Housing', 'expense', '🏠', '#795548'),
        ('Utilities', 'expense', '⚡', '#FF5722'),
        ('Healthcare', 'expense', '🏥', '#E91E63'),
        ('Entertainment', 'expense', '🎬', '#9C27B0'),
        ('Shopping', 'expense', '🛒', '#FF9800'),
        ('Education', 'expense', '📚', '#2196F3'),
        ('Insurance', 'expense', '🛡️', '#607D8B'),
        ('Fitness', 'expense', '💪', '#4CAF50'),
        ('Travel', 'expense', '✈️', '#00BCD4'),
        ('Personal Care', 'expense', '💅', '#E91E63'),
        ('Gifts & Donations', 'expense', '🎁', '#9C27B0'),
        ('Subscriptions', 'expense', '📱', '#FF5722'),
        ('Other Expenses', 'expense', '💸', '#607D8B')
    ]
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for name, cat_type, icon, color in default_categories:
            cursor.execute("""
                INSERT OR IGNORE INTO categories (name, type, icon, color, is_default) 
                VALUES (?, ?, ?, ?, TRUE)
            """, (name, cat_type, icon, color))
        
        conn.commit()
        logger.info(f"Default categories seeded successfully ({len(default_categories)} categories)")
        
    except sqlite3.Error as e:
        logger.error(f"Category seeding error: {e}")
        raise
    finally:
        conn.close()

# User Management Functions
def create_user(username: str, email: str, password_hash: str) -> Optional[int]:
    """
    Create a new user with default preferences and onboarding record.
    
    Args:
        username: Unique username (3-50 characters)
        email: Unique email address
        password_hash: Secure password hash
        
    Returns:
        User ID if successful, None if failed
        
    Raises:
        sqlite3.IntegrityError: If username or email already exists
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)
        """, (username, email, password_hash))
        
        user_id = cursor.lastrowid
        
        # Create default preferences
        cursor.execute("""
            INSERT INTO user_preferences (user_id) VALUES (?)
        """, (user_id,))
        
        # Create onboarding record
        cursor.execute("""
            INSERT INTO user_onboarding (user_id) VALUES (?)
        """, (user_id,))
        
        conn.commit()
        logger.info(f"User created successfully: {username} (ID: {user_id})")
        return user_id
        
    except sqlite3.IntegrityError as e:
        logger.error(f"User creation failed - duplicate: {e}")
        return None
    except sqlite3.Error as e:
        logger.error(f"User creation error: {e}")
        raise
    finally:
        conn.close()

def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
    """Get user by username."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, password_hash, created_at, last_login, is_active,
                   failed_login_attempts, locked_until
            FROM users 
            WHERE username = ? AND is_active = TRUE
        """, (username,))
        
        return cursor.fetchone()
        
    except sqlite3.Error as e:
        logger.error(f"Error fetching user by username: {e}")
        return None
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    """Get user by email address."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, password_hash, created_at, last_login, is_active
            FROM users 
            WHERE email = ? AND is_active = TRUE
        """, (email,))
        
        return cursor.fetchone()
        
    except sqlite3.Error as e:
        logger.error(f"Error fetching user by email: {e}")
        return None
    finally:
        conn.close()

def update_last_login(user_id: int) -> bool:
    """Update user's last login timestamp."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users 
            SET last_login = CURRENT_TIMESTAMP, failed_login_attempts = 0 
            WHERE id = ?
        """, (user_id,))
        
        conn.commit()
        return cursor.rowcount > 0
        
    except sqlite3.Error as e:
        logger.error(f"Error updating last login: {e}")
        return False
    finally:
        conn.close()

# Transaction Management Functions
def add_transaction(user_id: int, category_id: int, amount: float, 
                   transaction_type: str, description: str = '', 
                   date: str = None) -> Optional[int]:
    """
    Add a new transaction with validation.
    
    Args:
        user_id: User ID
        category_id: Category ID
        amount: Transaction amount (positive)
        transaction_type: 'income' or 'expense'
        description: Optional description
        date: Transaction date (YYYY-MM-DD) or None for today
        
    Returns:
        Transaction ID if successful, None if failed
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT INTO transactions (user_id, category_id, amount, type, description, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, category_id, amount, transaction_type, description, date))
        
        transaction_id = cursor.lastrowid
        conn.commit()
        
        logger.info(f"Transaction added: ID {transaction_id}, User {user_id}, Amount {amount}")
        return transaction_id
        
    except sqlite3.Error as e:
        logger.error(f"Transaction creation error: {e}")
        return None
    finally:
        conn.close()

def get_transactions(user_id: int, filters: Dict[str, Any] = None) -> List[sqlite3.Row]:
    """
    Get user's transactions with optional filtering and sorting.
    
    Args:
        user_id: User ID
        filters: Optional filters dict with keys:
            - type: 'income', 'expense', or 'all'
            - category_id: Category ID
            - start_date: Start date (YYYY-MM-DD)
            - end_date: End date (YYYY-MM-DD)
            - sort_by: 'date_desc', 'date_asc', 'amount_desc', 'amount_asc'
            
    Returns:
        List of transaction records with category information
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT t.*, c.name as category_name, c.icon as category_icon, c.color as category_color
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = ?
        """
        params = [user_id]
        
        # Apply filters
        if filters:
            if filters.get('type') and filters['type'] != 'all':
                query += " AND t.type = ?"
                params.append(filters['type'])
            
            if filters.get('category_id'):
                query += " AND t.category_id = ?"
                params.append(filters['category_id'])
            
            if filters.get('start_date'):
                query += " AND t.date >= ?"
                params.append(filters['start_date'])
            
            if filters.get('end_date'):
                query += " AND t.date <= ?"
                params.append(filters['end_date'])
        
        # Apply sorting
        sort_by = filters.get('sort_by', 'date_desc') if filters else 'date_desc'
        if sort_by == 'date_asc':
            query += " ORDER BY t.date ASC, t.created_at ASC"
        elif sort_by == 'amount_desc':
            query += " ORDER BY t.amount DESC"
        elif sort_by == 'amount_asc':
            query += " ORDER BY t.amount ASC"
        else:  # default: date_desc
            query += " ORDER BY t.date DESC, t.created_at DESC"
        
        # Limit for performance
        query += " LIMIT 1000"
        
        cursor.execute(query, params)
        return cursor.fetchall()
        
    except sqlite3.Error as e:
        logger.error(f"Error fetching transactions: {e}")
        return []
    finally:
        conn.close()

def update_transaction(transaction_id: int, user_id: int, data: Dict[str, Any]) -> bool:
    """Update a transaction (user must own it)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build dynamic update query
        set_clauses = []
        values = []
        
        allowed_fields = ['amount', 'type', 'category_id', 'description', 'date']
        
        for field, value in data.items():
            if field in allowed_fields:
                set_clauses.append(f"{field} = ?")
                values.append(value)
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        values.extend([transaction_id, user_id])
        
        query = f"""
            UPDATE transactions 
            SET {', '.join(set_clauses)} 
            WHERE id = ? AND user_id = ?
        """
        
        cursor.execute(query, values)
        conn.commit()
        
        return cursor.rowcount > 0
        
    except sqlite3.Error as e:
        logger.error(f"Error updating transaction: {e}")
        return False
    finally:
        conn.close()

def delete_transaction(transaction_id: int, user_id: int) -> bool:
    """Delete a transaction (user must own it)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM transactions 
            WHERE id = ? AND user_id = ?
        """, (transaction_id, user_id))
        
        conn.commit()
        return cursor.rowcount > 0
        
    except sqlite3.Error as e:
        logger.error(f"Error deleting transaction: {e}")
        return False
    finally:
        conn.close()

def search_transactions(user_id: int, search_term: str, 
                       filters: Dict[str, Any] = None) -> List[sqlite3.Row]:
    """
    Search transactions by description, amount, or category.
    
    Args:
        user_id: User ID
        search_term: Search query string
        filters: Optional additional filters
        
    Returns:
        List of matching transaction records
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT t.*, c.name as category_name, c.icon as category_icon, c.color as category_color
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = ?
            AND (
                t.description LIKE ? OR
                c.name LIKE ? OR
                CAST(t.amount AS TEXT) LIKE ?
            )
        """
        
        search_pattern = f'%{search_term}%'
        params = [user_id, search_pattern, search_pattern, search_pattern]
        
        # Apply additional filters
        if filters:
            if filters.get('type') and filters['type'] != 'all':
                query += " AND t.type = ?"
                params.append(filters['type'])
            
            if filters.get('category_id'):
                query += " AND t.category_id = ?"
                params.append(filters['category_id'])
            
            if filters.get('start_date'):
                query += " AND t.date >= ?"
                params.append(filters['start_date'])
            
            if filters.get('end_date'):
                query += " AND t.date <= ?"
                params.append(filters['end_date'])
        
        query += " ORDER BY t.date DESC, t.created_at DESC LIMIT 500"
        
        cursor.execute(query, params)
        return cursor.fetchall()
        
    except sqlite3.Error as e:
        logger.error(f"Error searching transactions: {e}")
        return []
    finally:
        conn.close()

def export_transactions_csv(user_id: int, filters: Dict[str, Any] = None) -> str:
    """Export transactions to CSV format."""
    try:
        transactions = get_transactions(user_id, filters)
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Date', 'Category', 'Type', 'Amount', 'Description', 'Created At'])
        
        # Write data
        for transaction in transactions:
            writer.writerow([
                transaction['date'],
                transaction['category_name'],
                transaction['type'].title(),
                transaction['amount'],
                transaction['description'] or '',
                transaction['created_at']
            ])
        
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error exporting transactions to CSV: {e}")
        return ""

# Budget Management Functions
def create_budget(user_id: int, category_id: int, amount: float, 
                 period: str = 'monthly', start_date: str = None) -> Optional[int]:
    """Create a new budget."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT OR REPLACE INTO budgets (user_id, category_id, amount, period, start_date)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, category_id, amount, period, start_date))
        
        budget_id = cursor.lastrowid
        conn.commit()
        
        logger.info(f"Budget created successfully with ID: {budget_id}")
        return budget_id
        
    except sqlite3.Error as e:
        logger.error(f"Budget creation error: {e}")
        raise
    finally:
        conn.close()

def get_user_budgets(user_id: int) -> List[sqlite3.Row]:
    """Get all active budgets for a user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.*, c.name as category_name, c.icon as category_icon, c.color as category_color
            FROM budgets b
            JOIN categories c ON b.category_id = c.id
            WHERE b.user_id = ? AND b.is_active = TRUE
            ORDER BY c.name
        """, (user_id,))
        
        return cursor.fetchall()
        
    except sqlite3.Error as e:
        logger.error(f"Error fetching user budgets: {e}")
        return []
    finally:
        conn.close()

def get_budget_performance(user_id: int, period: str = 'monthly') -> List[Dict[str, Any]]:
    """Get budget vs actual spending comparison."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current period dates
        now = datetime.now()
        if period == 'monthly':
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
            end_date = (now.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            end_date = end_date.strftime('%Y-%m-%d')
        else:
            # Default to current month
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
            end_date = (now.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            end_date = end_date.strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT 
                b.id as budget_id,
                b.amount as budget_amount,
                b.period,
                c.name as category_name,
                c.icon as category_icon,
                c.color as category_color,
                COALESCE(SUM(t.amount), 0) as actual_spent,
                b.amount - COALESCE(SUM(t.amount), 0) as remaining
            FROM budgets b
            JOIN categories c ON b.category_id = c.id
            LEFT JOIN transactions t ON b.category_id = t.category_id 
                AND t.user_id = b.user_id 
                AND t.type = 'expense'
                AND t.date >= ? 
                AND t.date <= ?
            WHERE b.user_id = ? AND b.is_active = TRUE AND b.period = ?
            GROUP BY b.id, b.amount, b.period, c.name, c.icon, c.color
            ORDER BY c.name
        """, (start_date, end_date, user_id, period))
        
        results = cursor.fetchall()
        
        budget_performance = []
        for row in results:
            percentage_used = (row['actual_spent'] / row['budget_amount']) * 100 if row['budget_amount'] > 0 else 0
            
            status = 'safe'
            if percentage_used >= 100:
                status = 'over'
            elif percentage_used >= 80:
                status = 'warning'
            elif percentage_used >= 60:
                status = 'caution'
            
            budget_performance.append({
                'budget_id': row['budget_id'],
                'category_name': row['category_name'],
                'category_icon': row['category_icon'],
                'category_color': row['category_color'],
                'budget_amount': row['budget_amount'],
                'actual_spent': row['actual_spent'],
                'remaining': row['remaining'],
                'percentage_used': round(percentage_used, 1),
                'status': status,
                'period': row['period']
            })
        
        return budget_performance
        
    except sqlite3.Error as e:
        logger.error(f"Error getting budget performance: {e}")
        return []
    finally:
        conn.close()

# Analytics Functions
def get_transaction_insights(user_id: int, period_days: int = 30) -> Dict[str, Any]:
    """Get transaction insights and analytics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
        
        insights = {}
        
        # Average daily spending
        cursor.execute("""
            SELECT AVG(daily_total) as avg_daily_spending
            FROM (
                SELECT DATE(date) as day, SUM(amount) as daily_total
                FROM transactions
                WHERE user_id = ? AND type = 'expense' 
                AND date >= ? AND date <= ?
                GROUP BY DATE(date)
            )
        """, (user_id, start_date, end_date))
        
        result = cursor.fetchone()
        insights['avg_daily_spending'] = result['avg_daily_spending'] or 0
        
        # Largest transaction
        cursor.execute("""
            SELECT amount, description, category_name, date, type
            FROM (
                SELECT t.amount, t.description, c.name as category_name, t.date, t.type,
                       ROW_NUMBER() OVER (ORDER BY t.amount DESC) as rn
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = ? AND t.date >= ? AND t.date <= ?
            )
            WHERE rn = 1
        """, (user_id, start_date, end_date))
        
        result = cursor.fetchone()
        if result:
            insights['largest_transaction'] = {
                'amount': result['amount'],
                'description': result['description'],
                'category': result['category_name'],
                'date': result['date'],
                'type': result['type']
            }
        
        # Top spending categories
        cursor.execute("""
            SELECT c.name as category_name, c.icon, SUM(t.amount) as total_amount
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = ? AND t.type = 'expense' 
            AND t.date >= ? AND t.date <= ?
            GROUP BY c.id, c.name, c.icon
            ORDER BY total_amount DESC
            LIMIT 5
        """, (user_id, start_date, end_date))
        
        insights['top_categories'] = cursor.fetchall()
        
        # Savings rate calculation
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense
            FROM transactions
            WHERE user_id = ? AND date >= ? AND date <= ?
        """, (user_id, start_date, end_date))
        
        result = cursor.fetchone()
        total_income = result['total_income'] or 0
        total_expense = result['total_expense'] or 0
        
        if total_income > 0:
            savings_rate = ((total_income - total_expense) / total_income) * 100
            insights['savings_rate'] = round(savings_rate, 1)
        else:
            insights['savings_rate'] = 0
            
        insights['total_income'] = total_income
        insights['total_expense'] = total_expense
        insights['net_savings'] = total_income - total_expense
        
        # Spending trends
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', date) as month,
                SUM(amount) as monthly_spending
            FROM transactions
            WHERE user_id = ? AND type = 'expense' 
            AND date >= date('now', '-6 months')
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month
        """, (user_id,))
        
        monthly_data = cursor.fetchall()
        if len(monthly_data) >= 2:
            recent_spending = monthly_data[-1]['monthly_spending']
            previous_spending = monthly_data[-2]['monthly_spending']
            
            if previous_spending > 0:
                trend_percentage = ((recent_spending - previous_spending) / previous_spending) * 100
                insights['spending_trend'] = {
                    'direction': 'increasing' if trend_percentage > 0 else 'decreasing',
                    'percentage': abs(round(trend_percentage, 1))
                }
            else:
                insights['spending_trend'] = {'direction': 'stable', 'percentage': 0}
        else:
            insights['spending_trend'] = {'direction': 'stable', 'percentage': 0}
        
        return insights
        
    except sqlite3.Error as e:
        logger.error(f"Error getting transaction insights: {e}")
        return {}
    finally:
        conn.close()

def get_category_breakdown(user_id: int, start_date: str, end_date: str) -> List[sqlite3.Row]:
    """Get category breakdown for charts."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.name as category_name,
                c.type as category_type,
                c.icon as category_icon,
                c.color as category_color,
                SUM(t.amount) as total_amount
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = ? AND t.date >= ? AND t.date <= ?
            GROUP BY c.id, c.name, c.type, c.icon, c.color
            HAVING total_amount > 0
            ORDER BY total_amount DESC
        """, (user_id, start_date, end_date))
        
        return cursor.fetchall()
        
    except sqlite3.Error as e:
        logger.error(f"Error getting category breakdown: {e}")
        return []
    finally:
        conn.close()

def get_income_expense_trends(user_id: int, months: int = 6) -> List[sqlite3.Row]:
    """Get income and expense trends over months."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', date) as month,
                type,
                SUM(amount) as total
            FROM transactions
            WHERE user_id = ? 
            AND date >= date('now', '-{} months')
            GROUP BY strftime('%Y-%m', date), type
            ORDER BY month
        """.format(months), (user_id,))
        
        return cursor.fetchall()
        
    except sqlite3.Error as e:
        logger.error(f"Error getting income expense trends: {e}")
        return []
    finally:
        conn.close()

def get_monthly_summary(user_id: int, year: int, month: int) -> Dict[str, float]:
    """Get monthly summary for dashboard stats."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Format month to have leading zero if needed
        month_str = f"{year}-{month:02d}"
        
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        """, (user_id, month_str))
        
        result = cursor.fetchone()
        
        income = result['income'] or 0
        expense = result['expense'] or 0
        
        return {
            'income': income,
            'expense': expense,
            'balance': income - expense
        }
        
    except sqlite3.Error as e:
        logger.error(f"Error getting monthly summary: {e}")
        return {'income': 0, 'expense': 0, 'balance': 0}
    finally:
        conn.close()

# Category Functions
def get_categories(category_type: str = None) -> List[sqlite3.Row]:
    """Get categories, optionally filtered by type."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if category_type:
            cursor.execute("""
                SELECT * FROM categories 
                WHERE type = ? 
                ORDER BY name
            """, (category_type,))
        else:
            cursor.execute("""
                SELECT * FROM categories 
                ORDER BY type, name
            """)
        
        return cursor.fetchall()
        
    except sqlite3.Error as e:
        logger.error(f"Error fetching categories: {e}")
        return []
    finally:
        conn.close()

def get_category_by_id(category_id: int) -> Optional[sqlite3.Row]:
    """Get a category by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM categories WHERE id = ?
        """, (category_id,))
        
        return cursor.fetchone()
        
    except sqlite3.Error as e:
        logger.error(f"Error fetching category: {e}")
        return None
    finally:
        conn.close()

def get_transaction_by_id(transaction_id: int, user_id: int) -> Optional[sqlite3.Row]:
    """Get a transaction by ID (user must own it)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.*, c.name as category_name
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.id = ? AND t.user_id = ?
        """, (transaction_id, user_id))
        
        return cursor.fetchone()
        
    except sqlite3.Error as e:
        logger.error(f"Error fetching transaction: {e}")
        return None
    finally:
        conn.close()

# User Preferences Functions
def get_user_preferences(user_id: int) -> Optional[sqlite3.Row]:
    """Get user preferences."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM user_preferences WHERE user_id = ?
        """, (user_id,))
        
        return cursor.fetchone()
        
    except sqlite3.Error as e:
        logger.error(f"Error fetching user preferences: {e}")
        return None
    finally:
        conn.close()

def update_user_preferences(user_id: int, preferences: Dict[str, Any]) -> bool:
    """Update user preferences."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build dynamic update query
        set_clauses = []
        values = []
        
        allowed_fields = ['currency', 'date_format', 'theme', 'default_view', 
                         'timezone', 'language', 'notifications_enabled', 'export_format']
        
        for field, value in preferences.items():
            if field in allowed_fields:
                set_clauses.append(f"{field} = ?")
                values.append(value)
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        values.append(user_id)
        
        query = f"""
            UPDATE user_preferences 
            SET {', '.join(set_clauses)} 
            WHERE user_id = ?
        """
        
        cursor.execute(query, values)
        conn.commit()
        
        return cursor.rowcount > 0
        
    except sqlite3.Error as e:
        logger.error(f"Error updating user preferences: {e}")
        return False
    finally:
        conn.close()

# Onboarding Functions
def get_user_onboarding(user_id: int) -> Optional[sqlite3.Row]:
    """Get user onboarding status."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM user_onboarding WHERE user_id = ?
        """, (user_id,))
        
        return cursor.fetchone()
        
    except sqlite3.Error as e:
        logger.error(f"Error fetching user onboarding: {e}")
        return None
    finally:
        conn.close()

def update_onboarding_progress(user_id: int, progress: Dict[str, bool]) -> bool:
    """Update user onboarding progress."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        set_clauses = []
        values = []
        
        allowed_fields = ['tour_completed', 'sample_data_added', 'first_transaction_added',
                         'first_budget_set', 'dashboard_visited', 'reports_visited',
                         'settings_visited', 'export_used', 'search_used', 'checklist_completed']
        
        for field, value in progress.items():
            if field in allowed_fields:
                set_clauses.append(f"{field} = ?")
                values.append(value)
        
        if not set_clauses:
            return False
        
        values.append(user_id)
        
        query = f"""
            UPDATE user_onboarding 
            SET {', '.join(set_clauses)}
            WHERE user_id = ?
        """
        
        cursor.execute(query, values)
        conn.commit()
        
        return cursor.rowcount > 0
        
    except sqlite3.Error as e:
        logger.error(f"Error updating onboarding progress: {e}")
        return False
    finally:
        conn.close()

def add_sample_data(user_id: int) -> bool:
    """Add sample transactions for new users."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get some category IDs
        cursor.execute("SELECT id, type FROM categories WHERE is_default = TRUE LIMIT 15")
        categories = cursor.fetchall()
        
        if not categories:
            return False
        
        # Create category lookup
        income_categories = [cat for cat in categories if cat['type'] == 'income']
        expense_categories = [cat for cat in categories if cat['type'] == 'expense']
        
        # Sample transactions with realistic data
        sample_transactions = [
            ('2025-09-25', income_categories[0]['id'] if income_categories else 1, 3000.00, 'income', 'Monthly Salary'),
            ('2025-09-24', expense_categories[0]['id'] if expense_categories else 5, 45.50, 'expense', 'Grocery shopping at Whole Foods'),
            ('2025-09-23', expense_categories[1]['id'] if len(expense_categories) > 1 else 6, 25.00, 'expense', 'Gas station fill-up'),
            ('2025-09-22', expense_categories[2]['id'] if len(expense_categories) > 2 else 7, 1200.00, 'expense', 'Monthly rent payment'),
            ('2025-09-21', expense_categories[3]['id'] if len(expense_categories) > 3 else 8, 75.00, 'expense', 'Doctor visit copay'),
            ('2025-09-20', expense_categories[4]['id'] if len(expense_categories) > 4 else 9, 35.00, 'expense', 'Movie night with friends'),
            ('2025-09-19', income_categories[1]['id'] if len(income_categories) > 1 else 2, 500.00, 'income', 'Freelance web design project'),
            ('2025-09-18', expense_categories[5]['id'] if len(expense_categories) > 5 else 10, 120.00, 'expense', 'Online shopping - clothes'),
            ('2025-09-17', expense_categories[0]['id'] if expense_categories else 5, 28.75, 'expense', 'Coffee shop and lunch'),
            ('2025-09-16', expense_categories[6]['id'] if len(expense_categories) > 6 else 11, 85.00, 'expense', 'Gym membership renewal'),
        ]
        
        # Insert sample transactions
        for date, category_id, amount, trans_type, description in sample_transactions:
            cursor.execute("""
                INSERT INTO transactions (user_id, category_id, amount, type, description, date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, category_id, amount, trans_type, description, date))
        
        # Update onboarding progress
        cursor.execute("""
            UPDATE user_onboarding 
            SET sample_data_added = TRUE 
            WHERE user_id = ?
        """, (user_id,))
        
        conn.commit()
        logger.info(f"Sample data added for user {user_id}")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error adding sample data: {e}")
        return False
    finally:
        conn.close()

# Initialize database on module import
if __name__ == "__main__":
    init_db()
    seed_default_categories()
    print("Enhanced database initialized and seeded successfully!")
