#!/bin/bash
set -e

echo "Running tests with pytest..."
pytest tests/ -v --tb=short

echo ""
echo "Tests completed successfully!"
