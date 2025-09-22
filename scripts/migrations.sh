#!/bin/bash
# Script to create database migrations

set -e

# Source directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$DIR")"

# Go to project root
cd "$PROJECT_ROOT"

# Check if docker-compose is running
if ! docker compose ps | grep -q "notification-service"; then
    echo "Error: Docker containers are not running. Start them with 'docker compose up -d'"
    exit 1
fi

# Get command
COMMAND=$1
ARGS="${@:2}"

if [ -z "$COMMAND" ]; then
    echo "Usage: $0 <command> [args]"
    echo "Commands:"
    echo "  init         - Initialize Aerich"
    echo "  migrate      - Create a new migration (requires name)"
    echo "  upgrade      - Upgrade database to the latest migration"
    exit 1
fi

# Run the appropriate command
case "$COMMAND" in
    init)
        echo "Initializing Aerich..."
        docker compose exec notification-service python -m scripts.aerich_init init
        ;;
    migrate)
        if [ -z "$2" ]; then
            echo "Error: Migration name is required"
            echo "Usage: $0 migrate <name>"
            exit 1
        fi
        echo "Creating migration: $2"
        docker compose exec notification-service python -m scripts.aerich_init migrate "$2"
        ;;
    upgrade)
        echo "Upgrading database..."
        docker compose exec notification-service python -m scripts.aerich_init upgrade
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Available commands: init, migrate, upgrade"
        exit 1
        ;;
esac