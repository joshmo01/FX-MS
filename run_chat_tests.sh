#!/bin/bash
# Script to run Chat API unit tests
# Usage: ./run_chat_tests.sh

set -e

echo "================================"
echo "  FX Chat API Unit Tests"
echo "================================"
echo ""

# Check if pytest is installed
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "❌ pytest not found. Installing dependencies..."
    pip install pytest pytest-asyncio
    echo ""
fi

# Run the tests
echo "Running tests..."
echo ""

python3 -m pytest tests/api/test_chat_api.py -v --tb=short

echo ""
echo "================================"
echo "  Test run complete!"
echo "================================"
