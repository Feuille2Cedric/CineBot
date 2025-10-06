from helper_functions.db import fetchrow, fetch

async def award_attempt(pool, user_id: int, day: int, correct: bool) -> None:
    # Insert or update scores_daily without altering schema; assumes schema has columns user_id, day, attempts, correct
    await fetch(pool, """
        INSERT INTO scores_daily (user_id, day, attempts, correct)
        VALUES ($1, $2, 1, $3)
        ON CONFLICT (user_id, day) DO UPDATE
        SET attempts = scores_daily.attempts + 1,
            correct = scores_daily.correct + EXCLUDED.correct
    """, user_id, day, 1 if correct else 0)

async def get_user_totals(pool, user_id: int) -> dict:
    row = await fetchrow(pool, """
        SELECT COALESCE(SUM(attempts),0) attempts, COALESCE(SUM(correct),0) correct
        FROM scores_daily
        WHERE user_id = $1
    """, user_id)
    attempts = int(row["attempts"]) if row else 0
    correct = int(row["correct"]) if row else 0
    rate = (100.0 * correct / attempts) if attempts else 0.0
    return {"attempts": attempts, "correct": correct, "rate": rate}

async def get_weekly_ranking(pool) -> list[tuple[int,int,int]]:
    rows = await fetch(pool, """
        SELECT user_id, COALESCE(SUM(correct),0) AS correct, COALESCE(SUM(attempts),0) AS attempts
        FROM scores_daily
        WHERE date_trunc('week', now())::date <= now()::date
        GROUP BY user_id
        ORDER BY correct DESC, attempts ASC
        LIMIT 20
    """)
    return [(int(r["user_id"]), int(r["correct"]), int(r["attempts"])) for r in rows]
