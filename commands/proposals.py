
import re
import discord
from discord.ext import commands
from helper_functions.quiz_repo import QuizRepo

def is_spoiler(text: str) -> bool:
    return text.startswith("||") and text.endswith("||")

def extract_question_reponse(content: str):
    match = re.search(r'Q\s*:\s*(.+?)R\s*:\s*(.+)', content, re.DOTALL | re.IGNORECASE)
    if match:
        question = match.group(1).strip()
        reponse = match.group(2).strip()
        return question, reponse
    return None, None

class ProposalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repo = QuizRepo(bot.db, bot.cfg.QUIZ_START_DATE)

    # ---------- COMMAND ----------
    @commands.command(name="propose")
    async def propose(self, ctx: commands.Context, *, question_et_reponse: str):
        if ctx.channel.id != self.bot.cfg.PROPOSAL_CHANNEL_ID:
            await ctx.send("Vous devez proposer les questions dans le salon approprié.")
            return
        if "|" not in question_et_reponse:
            await ctx.send("Format attendu : question | réponse")
            return
        question, reponse = [part.strip() for part in question_et_reponse.split("|", 1)]
        msg = await ctx.send(f"Proposition de question : {question}\nRéponse : ||{reponse}||\n\nAjoutez ✅ pour valider !")
        await msg.add_reaction('✅')

    # ---------- LISTENERS ----------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.channel.id == self.bot.cfg.PROPOSAL_CHANNEL_ID:
            content = message.content.strip()
            question, reponse = extract_question_reponse(content)
            if question and reponse:
                try:
                    if not is_spoiler(reponse):
                        await message.channel.send(
                            "❌ Merci de mettre la réponse en spoiler Discord, par exemple : `R: ||ma réponse||`"
                        )
                        return
                    await message.add_reaction('✅')
                except Exception:
                    pass

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User | discord.Member):
        if user.bot:
            return

        exclusive_emojis = ['✅', '❌', '🚮']
        if str(reaction.emoji) in exclusive_emojis:
            message = reaction.message
            for react in message.reactions:
                if (str(react.emoji) in exclusive_emojis and str(react.emoji) != str(reaction.emoji)):
                    users = [u async for u in react.users() if not u.bot]
                    if user in users:
                        try:
                            await message.remove_reaction(react.emoji, user)
                        except Exception:
                            pass

        # --- Suppression via 🚮 ---
        if str(reaction.emoji) == '🚮':
            try:
                if reaction.message.channel.id in [self.bot.cfg.VALIDATED_CHANNEL_ID, self.bot.cfg.COMMANDS_CHANNEL_ID]:
                    users = [u async for u in reaction.users() if not u.bot]
                    if len(users) >= 3:  # seuil identique à l'ancien code
                        content = reaction.message.content
                        match = re.search(r"\*\*Question :\*\* (.+?)\n\|\|", content, re.DOTALL)
                        if match:
                            question_text = match.group(1).strip()
                            async with self.bot.db.acquire() as conn:
                                await conn.execute("DELETE FROM questions WHERE question = $1", question_text)
                            await reaction.message.channel.send(f"🗑️ La question « {question_text} » a été supprimée après signalement.")
                        else:
                            await reaction.message.channel.send("Impossible de trouver le texte de la question pour la suppression.")
            except Exception:
                pass

        # --- Validation des propositions ---
        if reaction.message.channel.id == self.bot.cfg.PROPOSAL_CHANNEL_ID and str(reaction.emoji) == '✅':
            users = [u async for u in reaction.users() if not u.bot]
            if len(users) == self.bot.cfg.CHECKS_REQUIRED:
                content = reaction.message.content
                question, reponse = extract_question_reponse(content)
                if question and reponse:
                    if not is_spoiler(reponse):
                        await reaction.message.channel.send(
                            "❌ Merci de mettre la réponse en spoiler Discord, par exemple : `R: ||ma réponse||`"
                        )
                        return
                    if not question.endswith("?"):
                        question += " ?"
                    answer_text = reponse[2:-2].strip()
                    async with self.bot.db.acquire() as conn:
                        rows = await conn.fetch("SELECT 1 FROM questions WHERE question = $1", question)
                        if not rows:
                            await self.repo.save_question(question, answer_text)
                            await reaction.message.channel.send(
                                f"✅ Nouvelle question ajoutée à la base !\n**Q:** {question}\n**R:** ||{answer_text}||"
                            )
                        else:
                            await reaction.message.channel.send("Cette question existe déjà dans la base de données.")
                elif "Proposition de question :" in content and "Réponse :" in content:
                    question = content.split("Proposition de question :")[1].split("\n")[0].strip()
                    reponse = content.split("Réponse :")[1].split("||")[1].strip()
                    async with self.bot.db.acquire() as conn:
                        rows = await conn.fetch("SELECT 1 FROM questions WHERE question = $1", question)
                        if not rows:
                            await self.repo.save_question(question, reponse)
                            validated_channel = self.bot.get_channel(self.bot.cfg.VALIDATED_CHANNEL_ID)
                            if validated_channel:
                                await validated_channel.send(f"Question validée : {question}\nRéponse : ||{reponse}||")
                            await reaction.message.channel.send("Question ajoutée à la base de données !")
                        else:
                            await reaction.message.channel.send("Cette question existe déjà dans la base de données.")

        # --- Enregistrement des scores via réactions ---
        if reaction.message.channel.id == self.bot.cfg.VALIDATED_CHANNEL_ID:
            if reaction.message.content.startswith(f"<@&{self.bot.cfg.QUIZ_ROLE_ID}> Indiquez votre score"):
                emoji_to_score = {'0️⃣':0,'1️⃣':1,'2️⃣':2,'3️⃣':3,'4️⃣':4,'5️⃣':5,'6️⃣':6,'7️⃣':7,'8️⃣':8,'9️⃣':9,'🔟':10}
                if str(reaction.emoji) in emoji_to_score:
                    score = emoji_to_score[str(reaction.emoji)]
                    day = await self.repo.get_day_count()
                    await self.repo.save_score(user.id, day, 1, score, [])
