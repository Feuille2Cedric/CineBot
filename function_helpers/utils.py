import re
import datetime
from .constants import QUIZ_START_DATE

def is_spoiler(text: str) -> bool:
    return text.startswith("||") and text.endswith("||")

def extract_question_reponse(content: str):
    """
    Accepte:
      Q: ... R: ...
      Q : ... R : ...
    """
    match = re.search(r'Q\s*:\s*(.+?)R\s*:\s*(.+)', content, re.DOTALL | re.IGNORECASE)
    if match:
        question = match.group(1).strip()
        reponse  = match.group(2).strip()
        return question, reponse
    return None, None

def day_to_date(day_num: int) -> datetime.date:
    return QUIZ_START_DATE + datetime.timedelta(days=day_num - 1)
