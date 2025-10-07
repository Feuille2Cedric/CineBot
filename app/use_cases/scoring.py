import datetime
from typing import Dict
from app.domain.models import day_to_date
from app.domain.repositories import ScoreRepo
from config.settings import QUIZ_START_DATE, QUESTIONS_PAR_JOUR

async def compute_user_stats(repo: ScoreRepo, user_id: int) -> Dict:
    all_scores = await repo.fetch_all()
    now = datetime.datetime.now()

    daily = weekly = monthly = total = correct = total_q = 0
    for day_str, data in all_scores.get(str(user_id), {}).items():
        dnum = int(day_str)
        ddate = day_to_date(QUIZ_START_DATE, dnum)
        if ddate == now.date():
            daily += data["score"]
        if ddate.isocalendar()[1] == now.isocalendar()[1] and ddate.year == now.year:
            weekly += data["score"]
        if ddate.month == now.month and ddate.year == now.year:
            monthly += data["score"]
        total += data["score"]
        correct += data["score"]
        total_q += QUESTIONS_PAR_JOUR

    precision = (correct / total_q * 100) if total_q else 0

    leaderboard = []
    for uid, days in all_scores.items():
        t = sum(d["score"] for d in days.values())
        leaderboard.append((uid, t))
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    rank = next((i+1 for i, v in enumerate(leaderboard) if v[0] == str(user_id)), None)

    return dict(
        daily=daily, weekly=weekly, monthly=monthly, total=total,
        precision=precision, total_questions=total_q, rank=rank
    )
