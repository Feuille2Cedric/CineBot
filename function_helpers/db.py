import json
import random
import datetime

from .constants import (
    QUIZ_START_DATE, QUESTIONS_PAR_JOUR,
)

# ── Schéma ────────────────────────────────────────────────────────────────────
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

# ── Questions & Jour ──────────────────────────────────────────────────────────
async def get_questions(pool):
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT id, question, answer FROM questions")

async def save_question(pool, question: str, answer: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO questions (question, answer) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            question, answer
        )

async def get_random_question(pool):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT question, answer FROM questions ORDER BY random() LIMIT 1")

async def get_day_count(pool) -> int:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT day FROM day_count ORDER BY id DESC LIMIT 1")
        return row['day'] if row else 0

async def set_day_count(pool, day: int):
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO day_count(day) VALUES($1)", day)

async def get_jour_message(pool, day: int) -> str:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT message FROM messages_jour WHERE day=$1", day)
        if row:
            return row['message']
    return f"🎬 Jour {day} du quiz cinéma !"

# Gestion des questions non-répétées
async def get_unused_questions(pool):
    async with pool.acquire() as conn:
        return await conn.fetch("""
        SELECT id, question, answer
        FROM questions
        WHERE id NOT IN (SELECT question_id FROM used_questions)
    """)

async def mark_questions_used(pool, question_ids):
    async with pool.acquire() as conn:
        for qid in question_ids:
            await conn.execute(
                "INSERT INTO used_questions (question_id) VALUES ($1) ON CONFLICT DO NOTHING", qid
            )

async def reset_used_questions(pool):
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE used_questions")

# ── Scores ────────────────────────────────────────────────────────────────────
async def get_scores(pool):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM scores_daily")
    scores = {}
    for row in rows:
        uid = str(row['user_id'])
        day = str(row['day'])
        if uid not in scores:
            scores[uid] = {}
        scores[uid][day] = {
            "answered": row['answered'],
            "score": row['score'],
            "msg_ids": json.loads(row['msg_ids'])
        }
    return scores

async def save_score(pool, user_id, day, answered, score, msg_ids):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO scores_daily (user_id, day, answered, score, msg_ids)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id, day) DO UPDATE
            SET answered=$3, score=$4, msg_ids=$5
        """, int(user_id), int(day), answered, score, json.dumps(msg_ids))
