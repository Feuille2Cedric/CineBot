from helper_functions.db import fetch, fetchrow
from helper_functions.utils import answers_match

async def pick_random_questions(pool, n: int = 1) -> list[dict]:
    rows = await fetch(pool, "SELECT id, question, answer FROM questions ORDER BY random() LIMIT $1", n)
    return [dict(r) for r in rows]

async def get_current_day(pool) -> int:
    row = await fetchrow(pool, "SELECT day FROM day_count LIMIT 1")
    return int(row["day"]) if row else 1

async def get_message_for_day(pool, day: int) -> str | None:
    row = await fetchrow(pool, "SELECT message FROM messages_jour WHERE day = $1", day)
    return row["message"] if row else None

def is_correct(user_input: str, answer: str) -> bool:
    return answers_match(user_input, answer)
