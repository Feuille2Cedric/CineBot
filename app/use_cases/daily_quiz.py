import random
from typing import List
from app.domain.repositories import QuestionRepo
from config.settings import QUESTIONS_PAR_JOUR

async def pick_daily_ids(qrepo: QuestionRepo, weekday: int) -> List[int]:
    # 0=lundi ... 6=dimanche
    nb = 10 if weekday == 6 else QUESTIONS_PAR_JOUR
    qs = await qrepo.get_unused()
    if len(qs) < nb:
        await qrepo.reset_used()
        qs = await qrepo.get_unused()
    if len(qs) < nb:
        return []
    selected = random.sample(qs, nb)
    ids = [q.id for q in selected]
    await qrepo.mark_used(ids)
    return ids
