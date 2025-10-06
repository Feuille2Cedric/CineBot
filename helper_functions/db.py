import asyncpg
import logging
from typing import Any, Iterable

async def init_db(dsn: str, *, logger: logging.Logger) -> asyncpg.Pool:
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=10)
    logger.info("db_pool_ready")
    return pool

async def close_db(pool: "asyncpg.Pool") -> None:
    await pool.close()

async def fetch(pool, sql: str, *args) -> list[asyncpg.Record]:
    async with pool.acquire() as con:
        return await con.fetch(sql, *args)

async def fetchrow(pool, sql: str, *args) -> "asyncpg.Record | None":
    async with pool.acquire() as con:
        return await con.fetchrow(sql, *args)

async def fetchval(pool, sql: str, *args) -> Any:
    async with pool.acquire() as con:
        return await con.fetchval(sql, *args)

async def execute(pool, sql: str, *args) -> str:
    async with pool.acquire() as con:
        return await con.execute(sql, *args)

async def executemany(pool, sql: str, args_iter: Iterable[tuple]) -> None:
    async with pool.acquire() as con:
        await con.executemany(sql, args_iter)
