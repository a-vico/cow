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

Just restart the API:
```bash
docker compose --env-file .env restart api
```

## Local Development Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate 
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

### Run Tests
```bash
source venv/bin/activate
pytest -q
```

### Run Tests with Coverage
```bash
pytest tests/ --cov=app --cov-report=term-missing
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

### Cows
- `POST /api/v1/cows/` - Create a new cow
- `GET /api/v1/cows/` - List all cows
- `GET /api/v1/cows/{cow_id}` - Get a specific cow
- `DELETE /api/v1/cows/{cow_id}` - Delete a cow

### Measurements
- `POST /api/v1/measurements/` - Create a new measurement
- `GET /api/v1/measurements/` - List all measurements
- `GET /api/v1/measurements/{measurement_id}` - Get a specific measurement
- `DELETE /api/v1/measurements/{measurement_id}` - Delete a measurement

### Sensors
- `POST /api/v1/sensors/` - Create a new sensor
- `GET /api/v1/sensors/` - List all sensors
- `GET /api/v1/sensors/{sensor_id}` - Get a specific sensor
- `DELETE /api/v1/sensors/{sensor_id}` - Delete a sensor

### Reports
- `GET /api/v1/reports/weights` - Get cow weights report
- `GET /api/v1/reports/milk` - Get milk production report

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

4. Apply migrations (run inside the `api` container so it uses the same environment):

```bash
# Run Alembic from the api container
docker compose --env-file .env exec api alembic upgrade head

# Or run locally if your local env points to the recreated DB
alembic upgrade head
```

5. (Optional) Re-load initial data using the loader utilities:

```bash
python utils/load_data.py --data-dir data/input
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

## Utils

Small utility scripts live under `utils/`. Below are the primary helpers used during development and data loading.

### `read_sample_data.py` — quick Parquet inspection

- Purpose: Find Parquet files and print a short preview and summary for each.
- Location: `utils/read_sample_data.py`

CLI usage:

```bash
python utils/read_sample_data.py data/input
```

### `load_data.py` — bulk ASYNC loader (parquet → API)

- Purpose: Read `cows.parquet`, `sensors.parquet`, and `measurements.parquet` and POST them to the running API asynchronously.
- Location: `utils/load_data.py`

Important notes:
- The script POSTs cows and sensors by explicit IDs, and posts measurements to the measurements collection endpoint.
- Use `--dry-run` first to verify what will be sent (no network requests).
- The script takes around ~20 minutes to load 500K measurements.

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

