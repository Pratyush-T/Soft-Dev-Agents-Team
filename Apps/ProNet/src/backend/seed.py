"""Root-level seeder script and helper module for ProNet."""
import asyncio
from app.core.database import async_session_factory, init_db
from app.services.seeder import seed_database


async def main():
    await init_db()
    async with async_session_factory() as session:
        await seed_database(session, force=False)


if __name__ == "__main__":
    asyncio.run(main())
