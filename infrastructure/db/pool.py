import asyncpg
from config.settings import DATABASE_URL

async def create_pool():
    return await asyncpg.create_pool(DATABASE_URL)
