# Cow API

FastAPI application with PostgreSQL for managing items with full CRUD operations.

## Requirements

### For Docker (Recommended)
- [Docker](https://docs.docker.com/get-docker/) 20.10+
- [Docker Compose](https://docs.docker.com/compose/install/) 2.0+

### For Local Development
- Python 3.11+
- PostgreSQL 16+ (running locally or accessible)
- pip (Python package manager)

## Quick Start with Docker

### 1. Clone and Setup
```bash
cd /home/albertovico/repos/cow
cp .env.example .env
```

### 2. Build and Run
```bash
docker-compose up --build
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 3. Stop the Application
```bash
docker-compose down
```

To remove volumes (including database data):
```bash
docker-compose down -v
```

## Local Development Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -e ".[dev]"
```

### 3. Setup PostgreSQL
Make sure PostgreSQL is running locally and update `.env` file:
```bash
cp .env.example .env
# Edit .env with your local database credentials
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cow_db
```

### 4. Run Database Migrations
```bash
alembic upgrade head
```

### 5. Start the Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

## Running Tests

### With Virtual Environment
```bash
source venv/bin/activate
pytest tests/ -v
```

### Run Tests with Coverage
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

### Using Test Scripts
```bash
./scripts/test.sh              # Run tests
./scripts/test-coverage.sh     # Run tests with coverage report
```

## Project Structure

```
cow/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Application settings
│   ├── database.py          # Database connection and session
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   └── routes/
│       ├── __init__.py
│       └── items.py         # Item CRUD endpoints
├── alembic/
│   ├── versions/            # Database migration files
│   └── env.py              # Alembic configuration
├── tests/
│   ├── conftest.py         # Test fixtures
│   ├── test_main.py        # Main app tests
│   ├── test_items.py       # Item API tests
│   ├── test_models.py      # Database model tests
│   └── test_schemas.py     # Pydantic schema tests
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Application container
├── pyproject.toml          # Python dependencies
└── alembic.ini            # Alembic configuration
```

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

### Items CRUD
- `POST /api/v1/items/` - Create a new item
- `GET /api/v1/items/` - List all items (with pagination)
- `GET /api/v1/items/{item_id}` - Get a specific item
- `PUT /api/v1/items/{item_id}` - Update an item
- `DELETE /api/v1/items/{item_id}` - Delete an item

## API Documentation

Once the application is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@db:5432/cow_db` |
| `PROJECT_NAME` | API project name | `Cow API` |
| `VERSION` | API version | `0.1.0` |

## Database Migrations

### Create a New Migration
```bash
alembic revision --autogenerate -m "description of changes"
```

### Apply Migrations
```bash
alembic upgrade head
```

### Rollback Migration
```bash
alembic downgrade -1
```

## Development

### Code Formatting and Linting
```bash
# Format code
ruff format app/ tests/

# Lint code
ruff check app/ tests/
```

### Adding New Dependencies
```bash
# Edit pyproject.toml to add the dependency
# Then reinstall
pip install -e ".[dev]"
```

## Technology Stack

- **FastAPI** 0.115+ - Modern web framework
- **Python** 3.11+ - Programming language
- **PostgreSQL** 16+ - Database
- **SQLAlchemy** 2.0+ - ORM
- **Alembic** 1.14+ - Database migrations
- **Pydantic** 2.10+ - Data validation
- **Uvicorn** 0.32+ - ASGI server
- **Docker** & **Docker Compose** - Containerization
- **Pytest** 8.3+ - Testing framework

## Troubleshooting

### Docker Issues

**Port already in use:**
```bash
# Change ports in docker-compose.yml or stop the conflicting service
docker-compose down
```

**Database connection issues:**
```bash
# Check if database is healthy
docker-compose ps
# View database logs
docker-compose logs db
```

### Local Development Issues

**Import errors:**
```bash
# Make sure virtual environment is activated and package is installed
source venv/bin/activate
pip install -e ".[dev]"
```

**Database migration errors:**
```bash
# Check your DATABASE_URL in .env
# Ensure PostgreSQL is running
# Try to reset migrations (WARNING: this will delete data)
alembic downgrade base
alembic upgrade head
```

## License

This project is for educational purposes.

## Utils

This repository includes small utility scripts under `utils/` for local data inspection.

- `utils/read_sample_data.py`: Recursively scans a directory for Parquet files and prints a brief preview and summary for each file.

Usage (CLI):

```bash
# Scan current directory recursively
python utils/read_sample_data.py

# Scan a specific directory
python utils/read_sample_data.py data/input
```

Programmatic API:

```python
from utils.read_sample_data import read_parquet_files

# returns a dict: {"relative/path/to/file": pandas.DataFrame}
dfs = read_parquet_files("data/input")
```

Notes:

- The CLI prints the relative path, row/column counts and a small head() preview for each found Parquet file.
- The function `read_parquet_files` returns a mapping of relative file keys to DataFrames to be used in further processing.
