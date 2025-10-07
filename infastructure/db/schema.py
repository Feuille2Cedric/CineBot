SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scores_daily (
    user_id BIGINT NOT NULL,
    day INTEGER NOT NULL,
    answered INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0,
    msg_ids TEXT DEFAULT '[]',
    PRIMARY KEY (user_id, day)
);
CREATE TABLE IF NOT EXISTS day_count (
    id SERIAL PRIMARY KEY,
    day INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS messages_jour (
    day INTEGER PRIMARY KEY,
    message TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS used_questions (
    question_id INTEGER PRIMARY KEY
);
"""

async def ensure_schema(pool):
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA_SQL)
