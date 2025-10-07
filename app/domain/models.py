from dataclasses import dataclass
import datetime
from typing import List

@dataclass
class Question:
    id: int
    question: str
    answer: str

def day_to_date(start: datetime.date, day_num: int) -> datetime.date:
    return start + datetime.timedelta(days=day_num - 1)
