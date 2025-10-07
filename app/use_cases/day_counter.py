from app.domain.repositories import DayCounterRepo

async def next_day(counter: DayCounterRepo) -> int:
    d = await counter.get()
    nd = d + 1
    await counter.set(nd)
    return nd
