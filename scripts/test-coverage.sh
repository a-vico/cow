#!/bin/bash
set -e

echo "Running tests with coverage..."
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

echo ""
echo "Coverage report generated in htmlcov/index.html"
