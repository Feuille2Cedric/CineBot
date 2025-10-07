import re
import discord
from discord.ext import commands
from config.settings import (
    PROPOSAL_CHANNEL_ID, VALIDATED_CHANNEL_ID, COMMANDS_CHANNEL_ID,
    CHECKS_REQUIRED, QUIZ_ROLE_ID
)
from app.use_cases.questions import parse_q_r, is_spoiler
from app.domain.repositories import QuestionRepo, ScoreRepo, DayCounterRepo

class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.qrepo: QuestionRepo = bot.repos["questions"]
        self.srepo: ScoreRepo = bot.repos["scores"]
        self.drepo: DayCounterRepo = bot.repos["days"]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.channel.id == PROPOSAL_CHANNEL_ID:
            q, r = parse_q_r(message.content.strip())
            if q and r:
                if not is_spoiler(r):
                    await message.channel.send("❌ Merci de mettre la réponse en spoiler `||...||`.")
                    return
                try:
                    await message.add_reaction('✅')
                except Exception:
                    pass
        # NE PAS appeler process_commands ici

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return

        message = reaction.message

        # exclusivité ✅ ❌ 🚮
        if str(reaction.emoji) in ['✅','❌','🚮']:
            for react in message.reactions:
                if (str(react.emoji) in ['✅','❌','🚮'] 
                    and str(react.emoji) != str(reaction.emoji)):
                    users = [u async for u in react.users() if not u.bot]
                    if user in users:
                        try:
                            await message.remove_reaction(react.emoji, user)
                        except Exception as e:
                            print(f"Erreur retrait reaction: {e}")

        # suppression votée via 🚮
        if str(reaction.emoji) == '🚮' and message.channel.id in [VALIDATED_CHANNEL_ID, COMMANDS_CHANNEL_ID]:
            try:
                users = [u async for u in reaction.users() if not u.bot]
                if len(users) >= 3:
                    content = message.content
                    match = re.search(r"\*\*Question :\*\* (.+?)\n\|\|", content, re.DOTALL)
                    if match:
                        qtext = match.group(1).strip()
                        await self.qrepo.delete_by_text(qtext)
                        await message.channel.send(f"🗑️ La question « {qtext} » a été supprimée après signalement.")
                    else:
                        await message.channel.send("Impossible d'identifier la question à supprimer.")
            except Exception as e:
                print(f"Erreur suppression via 🚮 : {e}")

        # Validation dans PROPOSAL via ✅ au seuil CHECKS_REQUIRED
        if message.channel.id == PROPOSAL_CHANNEL_ID and str(reaction.emoji) == '✅':
            users = [u async for u in reaction.users() if not u.bot]
            if len(users) == CHECKS_REQUIRED:
                content = message.content
                q, r = parse_q_r(content)
                if not (q and r):
                    if "Proposition de question :" in content and "Réponse :" in content:
                        try:
                            q = content.split("Proposition de question :")[1].split("\n")[0].strip()
                            r = content.split("Réponse :")[1].split("||")[1].strip()
                            r = f"||{r}||"
                        except Exception:
                            q, r = None, None
                if q and r and is_spoiler(r):
                    if not q.endswith("?"):
                        q += " ?"
                    if not await self.qrepo.exists_question(q):
                        await self.qrepo.insert(q, r[2:-2].strip())
                        await message.channel.send(
                            f"✅ Nouvelle question ajoutée à la base !\n**Q:** {q}\n**R:** ||{r[2:-2].strip()}||"
                        )
                    else:
                        await message.channel.send("Cette question existe déjà dans la base de données.")
                else:
                    await message.channel.send("❌ Format invalide ou réponse non spoiler.")

        # Enregistrement du score quotidien
        if message.channel.id == VALIDATED_CHANNEL_ID:
            if message.content.startswith(f"<@&{QUIZ_ROLE_ID}> Indiquez votre score"):
                emoji_to_score = {
                    '0️⃣': 0,'1️⃣': 1,'2️⃣': 2,'3️⃣': 3,'4️⃣': 4,'5️⃣': 5,
                    '6️⃣': 6,'7️⃣': 7,'8️⃣': 8,'9️⃣': 9,'🔟': 10,
                }
                e = str(reaction.emoji)
                if e in emoji_to_score:
                    score = emoji_to_score[e]
                    day = await self.drepo.get()
                    await self.srepo.upsert(user.id, day, 1, score, [])

async def setup(bot: commands.Bot):
    if bot.get_cog("EventsCog") is None:
        await bot.add_cog(EventsCog(bot))
