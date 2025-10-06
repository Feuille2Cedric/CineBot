import discord

PRIMARY = 0x00A2FF
SUCCESS = 0x2ECC71
ERROR = 0xE74C3C
NEUTRAL = 0x95A5A6

def question_embed(q: dict) -> discord.Embed:
    emb = discord.Embed(title="Question 🎬", description=q["question"], color=PRIMARY)
    emb.set_footer(text=f"ID: {q['id']}")
    return emb

def result_embed(correct: bool, answer: str) -> discord.Embed:
    if correct:
        return discord.Embed(title="✅ Correct", description="Bien joué !", color=SUCCESS)
    else:
        return discord.Embed(title="❌ Incorrect", description=f"Réponse attendue: {answer}", color=ERROR)

def profile_embed(user, stats: dict) -> discord.Embed:
    emb = discord.Embed(title=f"Profil de {user.display_name}", color=PRIMARY)
    emb.add_field(name="Réussites", value=str(stats.get("correct", 0)))
    emb.add_field(name="Tentatives", value=str(stats.get("attempts", 0)))
    rate = stats.get("rate", 0.0)
    emb.add_field(name="Précision", value=f"{rate:.1f}%")
    return emb

def ranking_embed(title: str, lines: list[str]) -> discord.Embed:
    text = "\n".join(lines) if lines else "Aucune donnée."
    return discord.Embed(title=title, description=text, color=NEUTRAL)
