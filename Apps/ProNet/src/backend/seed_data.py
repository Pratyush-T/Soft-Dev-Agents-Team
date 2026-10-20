"""Deterministic database seeder entrypoint for ProNet.

Populates initial personas, connections, posts, comments, jobs, and applications.
"""
import asyncio
import logging
from app.core.database import async_session_factory, init_db
from app.services.seeder import seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pronet.seed_data")


async def main() -> None:
    """Run database table initialization and deterministic seeding."""
    logger.info("Initializing database schema...")
    await init_db()
    logger.info("Running deterministic seeder...")
    async with async_session_factory() as session:
        seeded = await seed_database(session, force=False)
        if seeded:
            logger.info("Database successfully seeded.")
        else:
            logger.info("Database already seeded. Skipping.")


if __name__ == "__main__":
    asyncio.run(main())
