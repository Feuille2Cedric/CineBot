
import json
import datetime
from typing import List, Dict, Any
import asyncpg

class QuizRepo:
    def __init__(self, pool: asyncpg.Pool, quiz_start_date: datetime.date):
        self.pool = pool
        self.quiz_start_date = quiz_start_date

    # questions
    async def get_questions(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT id, question, answer FROM questions")

    async def save_question(self, question: str, answer: str):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO questions (question, answer) VALUES ($1, $2) ON CONFLICT DO NOTHING", question, answer
            )

    async def get_random_question(self):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT question, answer FROM questions ORDER BY random() LIMIT 1")

    async def get_unused_questions(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("""
                SELECT id, question, answer
                FROM questions
                WHERE id NOT IN (SELECT question_id FROM used_questions)
            """)

    async def mark_questions_used(self, question_ids: list[int]):
        async with self.pool.acquire() as conn:
            for qid in question_ids:
                await conn.execute(
                    "INSERT INTO used_questions (question_id) VALUES ($1) ON CONFLICT DO NOTHING", qid
                )

    async def reset_used_questions(self):
        async with self.pool.acquire() as conn:
            await conn.execute("TRUNCATE used_questions")

    # day count
    async def get_day_count(self) -> int:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT day FROM day_count ORDER BY id DESC LIMIT 1")
            return row['day'] if row else 0

    async def set_day_count(self, day: int):
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO day_count(day) VALUES($1)", day)

    # messages
    async def get_jour_message(self, day: int) -> str:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT message FROM messages_jour WHERE day=$1", day)
            if row:
                return row['message']
            return f"🎬 Jour {day} du quiz cinéma !"

    # scores
    async def save_score(self, user_id: int, day: int, answered: int, score: int, msg_ids: list[str]):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO scores_daily (user_id, day, answered, score, msg_ids)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id, day) DO UPDATE
                SET answered=$3, score=$4, msg_ids=$5
            """, int(user_id), int(day), answered, score, json.dumps(msg_ids))

    async def get_scores(self) -> Dict[str, Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM scores_daily")
        scores: Dict[str, Dict[str, Any]] = {}
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

    # helpers
    def day_to_date(self, day_num: int) -> datetime.date:
        return self.quiz_start_date + datetime.timedelta(days=day_num - 1)
