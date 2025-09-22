#!/bin/bash

# Script to run mypy with correct configuration
# This avoids the configuration file issues

cd "$(dirname "$0")"

mypy \
  --ignore-missing-imports \
  --follow-imports=silent \
  --show-error-codes \
  --exclude='src/' \
  --python-version=3.13 \
  .

echo ""
echo "MyPy check completed."