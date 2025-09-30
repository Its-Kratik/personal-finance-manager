# Personal Finance Manager Pro

A comprehensive, secure personal finance management application built with Flask and modern web technologies.

## Features

- 📊 **Advanced Analytics** - Interactive charts and insights
- 🎯 **Budget Tracking** - Set limits and monitor spending
- 💰 **Transaction Management** - Full CRUD operations with categorization
- 📱 **Mobile Responsive** - Works perfectly on all devices
- 🔒 **Enterprise Security** - Rate limiting, CSRF protection, input sanitization
- 🌙 **Dark/Light Themes** - System preference detection
- ♿ **Accessibility** - WCAG 2.1 AA compliant
- 📊 **Data Export** - CSV export with custom filters
- 🔍 **Smart Search** - Real-time transaction search
- 🎯 **Onboarding** - Interactive welcome tour

## Quick Start

### Option 1: Docker (Recommended)

Clone repository
git clone <repository-url>
cd personal-finance-manager

Configure environment
cp .env.example .env

Edit .env with your settings
Start with Docker
docker-compose up -d

Initialize database
docker-compose exec web python -c "import model; model.init_db(); model.seed_default_categories()"

Access application
open http://localhost:8000

text

### Option 2: Local Development

Create virtual environment
python3 -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

Install dependencies
pip install -r requirements.txt

Set environment variables
export SECRET_KEY="your-secret-key"
export DATABASE_PATH="data/finance.db"

Create directories
mkdir -p data logs static/images

Initialize database
python -c "import model; model.init_db(); model.seed_default_categories()"

Run application
python controller.py

text

## Technology Stack

- **Backend**: Flask 2.3.3, SQLite
- **Frontend**: Vanilla JavaScript (ES6+), Chart.js
- **Security**: Flask-Talisman, Flask-Limiter
- **Styling**: Modern CSS with Glassmorphism
- **Deployment**: Docker, Gunicorn, Nginx

## Project Structure

personal-finance-manager/
├── controller.py # Main Flask application
├── model.py # Database operations
├── config.py # Configuration management
├── requirements.txt # Dependencies
├── templates/
│ └── index.html # Complete SPA template
├── static/
│ ├── css/style.css # Professional styling
│ ├── js/ # JavaScript modules
│ └── images/ # Assets and icons
├── data/ # Database storage
├── logs/ # Application logs
└── docs/ # Documentation

text

## Configuration

Key environment variables:

SECRET_KEY=your-super-secret-key
DATABASE_PATH=data/finance.db
FLASK_ENV=production
DEBUG=False
FORCE_HTTPS=True

text

## Security Features

- ✅ CSRF Protection with Content Security Policy
- ✅ Rate Limiting (5 req/min login, 100 req/min API)
- ✅ Input Sanitization & XSS Prevention
- ✅ SQL Injection Prevention
- ✅ Secure Password Hashing (pbkdf2:sha256)
- ✅ Session Security with HttpOnly/Secure flags
- ✅ HTTPS Enforcement

## API Documentation

See [API.md](API.md) for complete endpoint documentation.

## Testing

Run tests with:
pytest tests/

text

For coverage report:
coverage run -m pytest && coverage report

text

## Deployment

See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for production deployment guide.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details.
