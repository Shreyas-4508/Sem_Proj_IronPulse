# IronPulse

> AI-powered home fitness platform built with Python, Streamlit, and PostgreSQL.

## Features (Stage 1)

- Secure user registration and login (bcrypt password hashing)
- Personalized user profiles (fitness goals, body metrics, equipment, nutrition preferences)
- Onboarding wizard for first-time users
- Dark-themed responsive UI with IronPulse branding
- SQLite for development, PostgreSQL for production
- Alembic database migrations
- 41 automated tests covering authentication and profile functionality

## Quick Start (Local Development)

### Prerequisites

- Python 3.11 or later
- pip
- (Optional) PostgreSQL for production

### Installation

```bash
# 1. Clone or download the project
cd "d:\app fills\final montoring"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment (optional — SQLite is used by default)
copy .env.example .env
# Edit .env with your settings

# 4. Run the application
streamlit run app.py
```

The application will open at http://localhost:8501

## Configuration

Copy `.env.example` to `.env` and set the following:

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy DB URL | `sqlite:///./ironpulse_dev.db` |
| `SECRET_KEY` | App secret key | dev key (change in production!) |
| `OPENAI_API_KEY` | OpenAI API key for AI Coach | empty (Stage 3+) |
| `BCRYPT_ROUNDS` | Password hash cost | `12` |
| `APP_ENV` | `development` or `production` | `development` |

## PostgreSQL Setup

```bash
# Create database
createdb ironpulse_db

# Update .env
DATABASE_URL=postgresql://username:password@localhost:5432/ironpulse_db

# Run migrations
python -m alembic upgrade head
```

## Database Migrations

```bash
# Apply all pending migrations
python -m alembic upgrade head

# Create a new migration
python -m alembic revision --autogenerate -m "description"

# Rollback one migration
python -m alembic downgrade -1

# View migration history
python -m alembic history
```

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Run a specific test file
python -m pytest tests/test_stage1_auth.py -v
```

## Project Structure

```
ironpulse/
    app.py              — Main entry point
    config.py           — Settings from environment variables
    requirements.txt    — Python dependencies
    .env.example        — Environment template
    alembic.ini         — Migration configuration
    
    database/           — Connection and base model
    models/             — SQLAlchemy ORM models
    repositories/       — Database query helpers
    services/           — Business logic (auth, profile, etc.)
    pages/              — Streamlit page modules
    components/         — Shared UI components
    migrations/         — Alembic migration scripts
    tests/              — pytest test suite
```

## Deployment (Streamlit Community Cloud)

1. Push the project to a GitHub repository
2. Log in to [share.streamlit.io](https://share.streamlit.io)
3. Create a new app pointing to your repo and `app.py`
4. Add secrets in the Streamlit Cloud dashboard (Settings > Secrets):
   ```toml
   DATABASE_URL = "postgresql://..."
   SECRET_KEY = "your-production-secret"
   OPENAI_API_KEY = "sk-..."
   APP_ENV = "production"
   ```
5. Run Alembic migrations against your production database before launch

## Deployment (Render or Railway)

Both platforms support Python + PostgreSQL free tiers.

1. Connect your GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4. Add environment variables (DATABASE_URL, SECRET_KEY, etc.)
5. Run migrations: `python -m alembic upgrade head`

## Security Notes

- Never commit `.env` to version control (it is in `.gitignore`)
- Use a strong, random `SECRET_KEY` in production
- `BCRYPT_ROUNDS=12` (default) provides good security; increase for higher-value data
- All authorization checks are enforced in service functions, not just the UI
- Users can only access their own profile and data

## Technology Stack

- **Language:** Python 3.11+
- **Web Framework:** Streamlit
- **Database:** PostgreSQL (production) / SQLite (development)
- **ORM:** SQLAlchemy 2.x
- **Migrations:** Alembic
- **Password Hashing:** bcrypt
- **Data Validation:** Python (built-in validation in services)
- **Visualization:** Plotly (Stage 2+)
- **AI Integration:** OpenAI (Stage 3+)
- **Testing:** pytest

## Troubleshooting

**App won't start:**
- Ensure all packages from `requirements.txt` are installed
- Check Python version is 3.11 or later

**Database connection error:**
- For SQLite: the `.db` file is created automatically in the project directory
- For PostgreSQL: verify `DATABASE_URL` is correct and the database exists

**bcrypt error on Python 3.12+:**
- Use `bcrypt>=4.0.0` (already pinned in requirements.txt)

**Alembic migration fails:**
- Ensure `DATABASE_URL` is set before running `alembic upgrade head`
- For SQLite, `render_as_batch=True` is enabled automatically
