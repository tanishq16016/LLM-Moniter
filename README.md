# LLM Observability Dashboard

A comprehensive, production-ready LLM Observability Dashboard built with Django, PostgreSQL, Redis, and Bootstrap 5.

## Features

- **Real-time Monitoring**: Track all LLM API calls with detailed metrics
- **Cost Analysis**: Monitor spending across different models
- **Performance Metrics**: Latency tracking, token usage, and error rates
- **Interactive Testing**: Test LLM prompts directly from the dashboard
- **Analytics**: Comprehensive charts and data exports
- **User Feedback**: Collect ratings and comments on LLM responses

## Tech Stack

- **Backend**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL
- **Cache**: Redis
- **Frontend**: Bootstrap 5.3, Chart.js
- **LLM Provider**: Groq API

## Prerequisites

- Python 3.12+
- PostgreSQL (installed and running)
- Redis (installed and running)
- Groq API Key

## Installation

### 1. Clone the Repository

```bash
cd llm_monitor
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create PostgreSQL Database

```sql
-- Open pgAdmin or psql and run:
CREATE DATABASE llm_monitor_db;
```

### 5. Configure Environment Variables

```bash
# Copy example env file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Edit .env file with your settings
```

Generate an encryption key for API key storage:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

Update `.env` with:
- `SECRET_KEY`: Django secret key
- `DB_PASSWORD`: Your PostgreSQL password
- `ENCRYPTION_KEY`: Generated Fernet key

### 6. Run Migrations

```bash
python manage.py makemigrations dashboard
python manage.py migrate
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

### 8. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 9. Start Redis

```bash
# Linux
sudo systemctl start redis

# Windows (if using WSL or Docker)
redis-server
```

### 10. Run Development Server

```bash
python manage.py runserver
```

### 11. Access the Dashboard

- Dashboard: http://127.0.0.1:8000/
- Admin Panel: http://127.0.0.1:8000/admin/
- API Docs: http://127.0.0.1:8000/api/

## Configuration

### First-time Setup

1. Navigate to **Settings** page
2. Enter your Groq API key
3. Click **Save Key**
4. Click **Test Connection** to verify

### Available Model
- `llama-3.1-8b-instant` - Fast responses

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/traces/` | GET | List all traces (paginated) |
| `/api/traces/` | POST | Log a new LLM trace |
| `/api/traces/{id}/` | GET | Get trace details |
| `/api/feedback/` | POST | Submit feedback |
| `/api/analytics/overview/` | GET | Dashboard statistics |
| `/api/analytics/charts/` | GET | Chart data |
| `/api/config/groq-key/` | POST | Save API key |
| `/api/config/groq-key/` | GET | Check API key status |
| `/api/test-llm/` | POST | Test LLM call |

## Cost Tracking

Current pricing (per 1M tokens):

| Model | Input | Output |
|-------|-------|--------|
| Llama 3.1 70B | $0.59 | $0.79 |
| Llama 3.1 8B | $0.05 | $0.08 |
| Mixtral 8x7B | $0.24 | $0.24 |

## Development

### Running Tests

```bash
python manage.py test dashboard
```

### Code Structure

```
llm_monitor/
├── manage.py
├── llm_monitor/          # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── dashboard/            # Main application
│   ├── models.py         # Database models
│   ├── views.py          # API views
│   ├── serializers.py    # DRF serializers
│   ├── utils.py          # Utility functions
│   ├── templates/        # HTML templates
│   └── static/           # CSS/JS files
```

## Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running
- Verify database credentials in `.env`
- Check if database exists

### Redis Connection Error
- Ensure Redis is running
- Verify Redis URL in `.env`

### API Key Not Working
- Check if key is saved correctly in Settings
- Test connection from Settings page
- Verify Groq API key is valid

## License

MIT License

## Support

For issues and questions, please open a GitHub issue.
