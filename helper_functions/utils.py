import re

def normalize_answer(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("’", "'")
    return s

def answers_match(user_input: str, truth: str) -> bool:
    return normalize_answer(user_input) == normalize_answer(truth)
