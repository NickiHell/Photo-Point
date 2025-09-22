"""
Initialize Aerich migrations for the notification service.
"""

import asyncio
import logging
import sys
from pathlib import Path

from aerich import Command

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from app.infrastructure.config.tortoise_config import get_tortoise_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("aerich_init")


async def init_aerich() -> None:
    """Initialize Aerich for migrations."""
    logger.info("Initializing Aerich for database migrations...")
    
    config = get_tortoise_config()
    
    command = Command(
        tortoise_config=config,
        app="models",
        location=str(project_root / "migrations"),
    )
    
    # Initialize aerich
    await command.init()
    
    # Create initial migration
    await command.init_db(safe=True)
    
    logger.info("Aerich initialization completed successfully!")


async def create_migration(name: str) -> None:
    """Create a new migration."""
    logger.info(f"Creating migration: {name}")
    
    config = get_tortoise_config()
    
    command = Command(
        tortoise_config=config,
        app="models",
        location=str(project_root / "migrations"),
    )
    
    # Create a new migration
    await command.migrate(name)
    
    logger.info(f"Migration '{name}' created successfully!")


async def upgrade() -> None:
    """Upgrade database to the latest migration."""
    logger.info("Upgrading database to the latest migration...")
    
    config = get_tortoise_config()
    
    command = Command(
        tortoise_config=config,
        app="models",
        location=str(project_root / "migrations"),
    )
    
    # Upgrade to the latest migration
    await command.upgrade()
    
    logger.info("Database upgraded successfully!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.aerich_init <command> [args]")
        print("Commands:")
        print("  init - Initialize Aerich")
        print("  migrate <name> - Create a new migration")
        print("  upgrade - Upgrade database to the latest migration")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init":
        asyncio.run(init_aerich())
    elif command == "migrate":
        if len(sys.argv) < 3:
            print("Error: Migration name is required")
            print("Usage: python -m scripts.aerich_init migrate <name>")
            sys.exit(1)
        migration_name = sys.argv[2]
        asyncio.run(create_migration(migration_name))
    elif command == "upgrade":
        asyncio.run(upgrade())
    else:
        print(f"Unknown command: {command}")
        print("Available commands: init, migrate, upgrade")
        sys.exit(1)