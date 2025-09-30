# API Documentation

## Authentication Endpoints

### POST /login
Login user with username and password.

**Request:**
{
"username": "string",
"password": "string"
}



**Response:**
{
"success": true,
"user": {
"id": 1,
"username": "string",
"email": "string"
}
}



### POST /register
Register new user account.

**Request:**
{
"username": "string",
"email": "string",
"password": "string"
}



### GET /logout
Logout current user and clear session.

## Transaction Endpoints

### GET /transactions
Get user transactions with optional filtering.

**Query Parameters:**
- `type`: 'income', 'expense', or 'all'
- `category_id`: Filter by category
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)
- `sort_by`: 'date_desc', 'date_asc', 'amount_desc', 'amount_asc'

**Response:**
{
"transactions": [
{
"id": 1,
"amount": 100.50,
"type": "expense",
"description": "Grocery shopping",
"date": "2025-09-30",
"category_id": 1,
"category_name": "Food & Dining",
"created_at": "2025-09-30T10:00:00"
}
]
}



### POST /transactions
Create new transaction.

**Request:**
{
"type": "expense",
"amount": 100.50,
"category_id": 1,
"date": "2025-09-30",
"description": "Grocery shopping"
}



### PUT /transactions/{id}
Update existing transaction.

### DELETE /transactions/{id}
Delete transaction.

## Budget Endpoints

### GET /api/budgets
Get user budgets.

### POST /api/budgets
Create new budget.

**Request:**
{
"category_id": 1,
"amount": 500.00,
"period": "monthly",
"start_date": "2025-09-01"
}


### GET /api/budgets/performance
Get budget vs actual spending comparison.

## Category Endpoints

### GET /api/categories
Get all categories.

**Query Parameters:**
- `type`: Filter by 'income' or 'expense'

## Analytics Endpoints

### GET /api/chart-data
Get data for dashboard charts.

### GET /api/insights
Get financial insights and analytics.

### GET /api/search/transactions
Search transactions.

**Query Parameters:**
- `q`: Search query
- Additional filters same as /transactions

## User Endpoints

### GET /api/preferences
Get user preferences.

### PUT /api/preferences
Update user preferences.

### GET /api/onboarding
Get onboarding status.

### PUT /api/onboarding
Update onboarding progress.

## Export Endpoints

### GET /api/export/transactions
Export transactions to CSV.

## Rate Limits

- Login attempts: 5 per minute per IP
- API requests: 100 per minute per IP
- General requests: 1000 per hour per IP

## Error Responses

All endpoints return consistent error format:

{
"error": "Error message",
"message": "Detailed description"
}


**Status Codes:**
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 429: Rate Limit Exceeded
- 500: Internal Server Error
