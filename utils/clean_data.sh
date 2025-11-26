#!/usr/bin/env bash
set -euo pipefail

# clean_data.sh
# Run SQL DELETE statements directly against PostgreSQL to remove all
# rows from `measurements`, `sensors`, and `cows` tables.
# Usage: ./clean_data.sh [--dry-run] [--db-url <postgresql://user:pass@host:port/db>]

DB_URL="postgresql://postgres:postgres@localhost:5433/cow_db"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --db-url)
      DB_URL="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [--dry-run] [--db-url <url>]"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1"
      exit 1
      ;;
  esac
done

echo "DB_URL=${DB_URL}  DRY_RUN=${DRY_RUN}"

PSQL_CMD=""

if command -v psql >/dev/null 2>&1; then
  PSQL_CMD="psql '${DB_URL}' -v ON_ERROR_STOP=1 -q -t -A -f -"
else
  # try docker-compose exec as fallback (assumes service named db)
  if docker compose ps db >/dev/null 2>&1 || docker-compose ps db >/dev/null 2>&1; then
    # prefer docker compose if available
    if command -v docker >/dev/null 2>&1; then
      # use docker compose exec into the db container
      # find container id for service named 'db'
      CONTAINER=$(docker ps --filter "name=cow_db_1" --format "{{.ID}}" | head -n1 || true)
      if [ -n "$CONTAINER" ]; then
        PSQL_CMD="docker exec -i ${CONTAINER} psql -U postgres -d cow_db -v ON_ERROR_STOP=1 -q -t -A -f -"
      else
        # fallback to docker-compose service name
        PSQL_CMD="docker-compose exec -T db psql -U postgres -d cow_db -v ON_ERROR_STOP=1 -q -t -A -f -"
      fi
    fi
  fi
fi

SQL_CMDS=(
  "BEGIN;" 
  "DELETE FROM measurements;" 
  "ALTER SEQUENCE measurements_id_seq RESTART WITH 1;" 
  "DELETE FROM sensors;" 
  "DELETE FROM cows;" 
  "COMMIT;"
)

if [ "$DRY_RUN" = true ]; then
  echo "DRY-RUN: The following SQL would be executed:"
  for s in "${SQL_CMDS[@]}"; do
    echo "  $s"
  done
  exit 0
fi

if [ -z "$PSQL_CMD" ]; then
  echo "Error: no psql found and no docker container detected to exec into. Install psql or run this from the compose host." >&2
  exit 1
fi

FULL_SQL="$(printf "%s\n" "${SQL_CMDS[@]}")"

echo "Executing SQL against database..."
echo "$FULL_SQL" | eval ${PSQL_CMD}

echo "Done."
