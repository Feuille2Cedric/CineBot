from typing import Optional, Tuple
import re
from app.domain.repositories import QuestionRepo

SPOILER_OPEN = "||"
SPOILER_CLOSE = "||"

def parse_q_r(raw: str) -> Tuple[Optional[str], Optional[str]]:
    m = re.search(r'Q\s*:\s*(.+?)R\s*:\s*(.+)', raw, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    if "|" in raw:
        q, r = raw.split("|", 1)
        return q.strip(), r.strip()
    return None, None

def is_spoiler(text: str) -> bool:
    return text.startswith(SPOILER_OPEN) and text.endswith(SPOILER_CLOSE)

def strip_spoiler(text: str) -> str:
    return text[len(SPOILER_OPEN):-len(SPOILER_CLOSE)].strip()

async def add_question_if_new(repo: QuestionRepo, question: str, answer_spoilered: str) -> str:
    if not is_spoiler(answer_spoilered):
        return "not_spoiler"
    if not question.endswith("?"):
        question += " ?"
    answer = strip_spoiler(answer_spoilered)
    if await repo.exists_question(question):
        return "exists"
    await repo.insert(question, answer)
    return "added"
