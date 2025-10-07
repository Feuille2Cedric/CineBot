import json
from typing import List, Optional, Dict, Any
from app.domain.models import Question
from app.domain.repositories import QuestionRepo, DayCounterRepo, DailyMessageRepo, ScoreRepo

class PgQuestionRepo(QuestionRepo):
    def __init__(self, pool):
        self.pool = pool

    async def all(self) -> List[Question]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, question, answer FROM questions")
        return [Question(r["id"], r["question"], r["answer"]) for r in rows]

    async def insert(self, question: str, answer: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO questions (question, answer) VALUES ($1,$2) ON CONFLICT DO NOTHING",
                question, answer
            )

    async def random_qa(self) -> Optional[Question]:
        async with self.pool.acquire() as conn:
            r = await conn.fetchrow("SELECT id, question, answer FROM questions ORDER BY random() LIMIT 1")
        return Question(r["id"], r["question"], r["answer"]) if r else None

    async def exists_question(self, question: str) -> bool:
        async with self.pool.acquire() as conn:
            r = await conn.fetchrow("SELECT 1 FROM questions WHERE question=$1", question)
        return bool(r)

    async def delete_by_text(self, question_text: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM questions WHERE question=$1", question_text)

    async def get_unused(self) -> List[Question]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, question, answer
                FROM questions
                WHERE id NOT IN (SELECT question_id FROM used_questions)
            """)
        return [Question(r["id"], r["question"], r["answer"]) for r in rows]

    async def mark_used(self, ids: List[int]) -> None:
        async with self.pool.acquire() as conn:
            for qid in ids:
                await conn.execute(
                    "INSERT INTO used_questions (question_id) VALUES ($1) ON CONFLICT DO NOTHING", qid
                )

    async def reset_used(self) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("TRUNCATE used_questions")

    async def get_by_ids(self, ids: List[int]) -> List[Question]:
        if not ids:
            return []
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, question, answer FROM questions WHERE id = ANY($1::int[])",
                ids
            )
        id_to_q = {r["id"]: Question(r["id"], r["question"], r["answer"]) for r in rows}
        return [id_to_q[i] for i in ids if i in id_to_q]

class PgDayCounterRepo(DayCounterRepo):
    def __init__(self, pool):
        self.pool = pool

    async def get(self) -> int:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT day FROM day_count ORDER BY id DESC LIMIT 1")
            return row['day'] if row else 0

    async def set(self, day: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO day_count(day) VALUES($1)", day)

class PgDailyMessageRepo(DailyMessageRepo):
    def __init__(self, pool):
        self.pool = pool

    async def get_by_day(self, day: int) -> str:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT message FROM messages_jour WHERE day=$1", day)
            if row:
                return row['message']
        return f"🎬 Jour {day} du quiz cinéma !"

class PgScoreRepo(ScoreRepo):
    def __init__(self, pool):
        self.pool = pool

    async def fetch_all(self) -> Dict[str, Dict[str, Any]]:
        async with self.pool.acquire() as conn:
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

    async def upsert(self, user_id: int, day: int, answered: int, score: int, msg_ids: list) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO scores_daily (user_id, day, answered, score, msg_ids)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id, day) DO UPDATE
                SET answered=$3, score=$4, msg_ids=$5
            """, int(user_id), int(day), answered, score, json.dumps(msg_ids))

    async def fetch_rows(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id, day, score FROM scores_daily")
        return [dict(r) for r in rows]
