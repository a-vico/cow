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
docker compose --env-file .env up -d
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
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cow_db
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
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@db:5432/cow_db` |
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

## Recreate Database (Destroy & Recreate)

Warning: these steps will permanently delete the database data stored in the Docker volume. Only run on development or throwaway environments unless you have backups.

1. Stop containers and remove volumes (this destroys DB data):

```bash
# Stop services and remove volumes (DB data removed)
docker compose --env-file .env down -v
```

2. Rebuild and start services (this will recreate the DB container and empty database):

```bash
docker compose --env-file .env up -d --build
```

3. Wait for the database to become healthy (simple `ps` check):

```bash
docker compose --env-file .env ps
# or a loop that waits for Postgres readiness (inside the db container):
until docker compose --env-file .env exec db pg_isready -U "$POSTGRES_USER"; do sleep 1; done
```

4. Apply migrations (run inside the `api` container so it uses the same environment):

```bash
# Run Alembic from the api container
docker compose --env-file .env exec api alembic upgrade head

# Or run locally if your local env points to the recreated DB
alembic upgrade head
```

5. (Optional) Re-load initial data using the loader utilities:

```bash
# Dry-run first
python utils/load_data.py --data-dir data/input --dry-run
# Then load for real
python utils/load_data.py --data-dir data/input
```

If your setup runs Alembic automatically on API startup (some deployments do), step 4 may not be necessary.


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

## Utils

Small utility scripts live under `utils/`. Below are the primary helpers used during development and data loading.

### `read_sample_data.py` — quick Parquet inspection

- Purpose: Find Parquet files and print a short preview and summary for each.
- Location: `utils/read_sample_data.py`

CLI usage:

```bash
# Scan current directory recursively
python utils/read_sample_data.py

# Scan a specific directory
python utils/read_sample_data.py data/input
```

Programmatic:

```python
from utils.read_sample_data import read_parquet_files
dfs = read_parquet_files("data/input")
```

### `load_data.py` — bulk loader (parquet → API)

- Purpose: Read `cows.parquet`, `sensors.parquet`, and `measurements.parquet` and POST them to the running API.
- Location: `utils/load_data.py`

Important notes:
- The script POSTs cows and sensors by explicit IDs, and posts measurements to the measurements collection endpoint.
- Use `--dry-run` first to verify what will be sent (no network requests).

CLI usage:

```bash
# Dry-run (prints payloads only)
python utils/load_data.py --data-dir data/input --dry-run

# Real run (performs HTTP POSTs)
python utils/load_data.py --data-dir data/input
```

Options:
- `--data-dir` (default: `data/input`) — directory with `cows.parquet`, `sensors.parquet`, `measurements.parquet`.
- `--dry-run` — print HTTP payloads without sending requests.

Example: do a dry-run, then load data for real:

```bash
python utils/load_data.py --data-dir data/input --dry-run
python utils/load_data.py --data-dir data/input
```

### `clean_data.sh` — destructive DB wipe (SQL)

- Purpose: Remove all rows from `measurements`, `sensors`, and `cows` in the development DB. This runs SQL directly against Postgres (faster and avoids API-level validation).
- Location: `utils/clean_data.sh`

WARNING: Destructive operation. Always run with `--dry-run` first and ensure you have backups if needed.

CLI usage:

```bash
# Show SQL to be executed (safe)
./utils/clean_data.sh --dry-run

# Execute against the default local DB
./utils/clean_data.sh

# Execute against a custom DB URL
./utils/clean_data.sh --db-url postgresql://user:pass@host:port/dbname
```

Options:
- `--db-url` — Postgres connection string (default: `postgresql+asyncpg://postgres:postgres@localhost:5433/cow_db`).
- `--dry-run` — print the SQL and exit.

Behavior details:
- If `psql` is installed locally the script pipes SQL into it.
- If `psql` is missing the script will attempt to exec into the running `db` container (`docker exec` / `docker-compose exec`) and run `psql` there.

Suggested workflow for reloading data:

1. Stop API hot-reload or avoid editing watched files while loading.
2. Confirm DB state and run a dry-run:

```bash
./utils/clean_data.sh --dry-run
```

3. If satisfied, run the destructive step (or run against a throwaway DB):

```bash
./utils/clean_data.sh
```

4. Load the parquet data (dry-run first if desired):

```bash
python utils/load_data.py --data-dir data/input --dry-run
python utils/load_data.py --data-dir data/input
```
