import asyncio
import random
import re
import datetime
import discord
from discord.ext import commands, tasks

from function_helpers.constants import (
    PROPOSAL_CHANNEL_ID, VALIDATED_CHANNEL_ID, COMMANDS_CHANNEL_ID, UPDATE_CHANNEL_ID,
    QUIZ_ROLE_ID, CHECKS_REQUIRED, QUESTIONS_PAR_JOUR,
    HOUR_QUESTIONS_DAILY, MINUTE_QUESTIONS_DAILY,
)
from function_helpers import db as dbh
from function_helpers import utils as U

class QuizCog(commands.Cog, name="QuizCog"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # démarrer la tâche quotidienne si pas déjà lancée
        if not self.daily_questions.is_running():
            self.daily_questions.start()

    # ───────────────────────── Events ─────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel.id == PROPOSAL_CHANNEL_ID:
            content = message.content.strip()
            question, reponse = U.extract_question_reponse(content)
            if question and reponse:
                if not U.is_spoiler(reponse):
                    await message.channel.send(
                        "❌ Merci de mettre la réponse en spoiler Discord, par exemple : `R: ||ma réponse||`"
                    )
                    return
                try:
                    await message.add_reaction('✅')
                except Exception:
                    pass

        await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return

        # exclusivité de réactions ✅ ❌ 🚮
        exclusive_emojis = ['✅', '❌', '🚮']
        if str(reaction.emoji) in exclusive_emojis:
            message = reaction.message
            for react in message.reactions:
                if (str(react.emoji) in exclusive_emojis
                    and str(react.emoji) != str(reaction.emoji)):
                    users = [u async for u in react.users() if not u.bot]
                    if user in users:
                        try:
                            await message.remove_reaction(react.emoji, user)
                        except Exception as e:
                            print(f"Erreur retrait reaction: {e}")

        # Suppression via 🚮
        if str(reaction.emoji) == '🚮':
            try:
                if reaction.message.channel.id in [VALIDATED_CHANNEL_ID, COMMANDS_CHANNEL_ID]:
                    users = [u async for u in reaction.users() if not u.bot]
                    print(f"[DEBUG] 🚮 votes sur {reaction.message.id} : {[u.id for u in users]}")
                    if len(users) >= 3:
                        content = reaction.message.content
                        match = re.search(r"\*\*Question :\*\* (.+?)\n\|\|", content, re.DOTALL)
                        if match:
                            question_text = match.group(1).strip()
                            async with self.bot.db.acquire() as conn:
                                await conn.execute("DELETE FROM questions WHERE question = $1", question_text)
                            await reaction.message.channel.send(
                                f"🗑️ La question « {question_text} » a été supprimée après signalement."
                            )
                        else:
                            await reaction.message.channel.send(
                                "Impossible de trouver le texte de la question pour la suppression."
                            )
            except Exception as e:
                print(f"Erreur suppression via 🚮 : {e}")

        # Validation des propositions via ✅
        if reaction.message.channel.id == PROPOSAL_CHANNEL_ID and str(reaction.emoji) == '✅':
            users = [u async for u in reaction.users() if not u.bot]
            if len(users) == CHECKS_REQUIRED:
                content = reaction.message.content
                question, reponse = U.extract_question_reponse(content)
                if question and reponse:
                    if not U.is_spoiler(reponse):
                        await reaction.message.channel.send(
                            "❌ Merci de mettre la réponse en spoiler Discord, par exemple : `R: ||ma réponse||`"
                        )
                        return
                    if not question.endswith("?"):
                        question += " ?"
                    answer_text = reponse[2:-2].strip()
                    rows = await self.bot.db.fetch("SELECT 1 FROM questions WHERE question = $1", question)
                    if not rows:
                        await dbh.save_question(self.bot.db, question, answer_text)
                        await reaction.message.channel.send(
                            f"✅ Nouvelle question ajoutée à la base !\n**Q:** {question}\n**R:** ||{answer_text}||"
                        )
                    else:
                        await reaction.message.channel.send("Cette question existe déjà dans la base de données.")
                elif "Proposition de question :" in content and "Réponse :" in content:
                    question = content.split("Proposition de question :")[1].split("\n")[0].strip()
                    reponse = content.split("Réponse :")[1].split("||")[1].strip()
                    rows = await self.bot.db.fetch("SELECT 1 FROM questions WHERE question = $1", question)
                    if not rows:
                        await dbh.save_question(self.bot.db, question, reponse)
                        validated_channel = self.bot.get_channel(VALIDATED_CHANNEL_ID)
                        if validated_channel:
                            await validated_channel.send(f"Question validée : {question}\nRéponse : ||{reponse}||")
                        await reaction.message.channel.send("Question ajoutée à la base de données !")
                    else:
                        await reaction.message.channel.send("Cette question existe déjà dans la base de données.")

        # Enregistrement du score quotidien via réactions
        if reaction.message.channel.id == VALIDATED_CHANNEL_ID:
            if reaction.message.content.startswith(f"<@&{QUIZ_ROLE_ID}> Indiquez votre score"):
                emoji_to_score = {
                    '0️⃣': 0,'1️⃣': 1,'2️⃣': 2,'3️⃣': 3,'4️⃣': 4,'5️⃣': 5,
                    '6️⃣': 6,'7️⃣': 7,'8️⃣': 8,'9️⃣': 9,'🔟': 10,
                }
                if str(reaction.emoji) in emoji_to_score:
                    score = emoji_to_score[str(reaction.emoji)]
                    day = await dbh.get_day_count(self.bot.db)
                    await dbh.save_score(self.bot.db, user.id, day, 1, score, [])
                    print(f"[DEBUG] Score enregistré : user={user.id}, day={day}, score={score}")

    # ──────────────────────── Commandes ────────────────────────
    @commands.command()
    async def propose(self, ctx, *, question_et_reponse: str):
        if ctx.channel.id != PROPOSAL_CHANNEL_ID:
            await ctx.send("Vous devez proposer les questions dans le salon approprié.")
            return
        if "|" not in question_et_reponse:
            await ctx.send("Format attendu : question | réponse")
            return
        question, reponse = [part.strip() for part in question_et_reponse.split("|", 1)]
        msg = await ctx.send(
            f"Proposition de question : {question}\nRéponse : ||{reponse}||\n\nAjoutez ✅ pour valider !"
        )
        await msg.add_reaction('✅')

    @commands.command()
    async def q(self, ctx):
        if ctx.channel.id != COMMANDS_CHANNEL_ID:
            await ctx.send("Cette commande n'est autorisée que dans le salon de commandes.")
            return
        row = await dbh.get_random_question(self.bot.db)
        if not row:
            await ctx.send("Aucune question disponible.")
            return
        msg = await ctx.send(f"**Question :** {row['question']}\n||{row['answer']}||")
        for e in ('✅', '❌', '🚮'):
            await msg.add_reaction(e)

    @commands.command()
    async def sp(self, ctx):
        scores = await dbh.get_scores(self.bot.db)
        user_id = str(ctx.author.id)
        now = datetime.datetime.now()
        daily = weekly = monthly = total = correct = total_questions = 0

        for day_str, data in scores.get(user_id, {}).items():
            day_num = int(day_str)
            day_date = U.day_to_date(day_num)
            if day_date == now.date():
                daily += data["score"]
            if day_date.isocalendar()[1] == now.isocalendar()[1] and day_date.year == now.year:
                weekly += data["score"]
            if day_date.month == now.month and day_date.year == now.year:
                monthly += data["score"]
            total += data["score"]
            correct += data["score"]
            total_questions += QUESTIONS_PAR_JOUR

        precision = (correct / total_questions * 100) if total_questions else 0

        # leaderboard global
        leaderboard = []
        for uid, days in scores.items():
            t = sum(d["score"] for d in days.values())
            leaderboard.append((uid, t))
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        rank = next((i+1 for i, v in enumerate(leaderboard) if v[0] == user_id), None)

        embed = discord.Embed(
            title=f"Profil de {ctx.author.name} 📊",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="📅 Score quotidien", value=f"{daily} points", inline=False)
        embed.add_field(name="📆 Score hebdomadaire", value=f"{weekly} points", inline=False)
        embed.add_field(name="🗓️ Score mensuel", value=f"{monthly} points", inline=False)
        embed.add_field(name="🏆 Score total", value=f"{total} points", inline=False)
        embed.add_field(name="🎯 Précision", value=f"{precision:.2f}%", inline=False)
        embed.add_field(name="💯 Total de questions répondues", value=f"{total_questions} questions", inline=False)
        if rank:
            embed.set_footer(text=f"Tu es classé #{rank} total avec {total} points !")
        await ctx.send(embed=embed)

    @commands.command()
    async def sr(self, ctx, *, mode: str = "weekly"):
        now = datetime.datetime.now()
        embed = discord.Embed()
        leaderboard = {}
        rows = await self.bot.db.fetch("SELECT user_id, day, score FROM scores_daily")

        mode_clean = mode.lower().replace(" ", "")
        if mode_clean == "alltime":
            for row in rows:
                uid = str(row["user_id"])
                leaderboard[uid] = leaderboard.get(uid, 0) + row["score"]
            embed.title = "🏅 Classement Global – Tous Temps"
            embed.color = discord.Color.purple()
        else:
            current_week = now.isocalendar()[1]
            current_year = now.year
            for row in rows:
                day_date = U.day_to_date(row["day"])
                if day_date.isocalendar()[1] == current_week and day_date.year == current_year:
                    uid = str(row["user_id"])
                    leaderboard[uid] = leaderboard.get(uid, 0) + row["score"]
            embed.title = "🏆 Classement Weekly 🏆"
            embed.color = discord.Color.gold()

        sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
        desc = ""
        for i, (uid, score) in enumerate(sorted_lb[:20], 1):
            try:
                user = await self.bot.fetch_user(int(uid))
                name = user.name
            except Exception:
                name = f"Utilisateur {uid}"
            desc += f"**{i}**. {name} — **{score} points**\n"
        embed.description = desc

        user_id = str(ctx.author.id)
        user_rank = next((i+1 for i, v in enumerate(sorted_lb) if v[0] == user_id), None)
        user_score = leaderboard.get(user_id, 0)
        if user_rank:
            suffix = "au total" if mode_clean == "alltime" else "cette semaine"
            embed.set_footer(text=f"{ctx.author.name} est classé #{user_rank} {suffix} avec {user_score} points.")
        await ctx.send(embed=embed)

    @commands.command()
    async def annonce_nouveautes(self, ctx):
        if ctx.channel.id != UPDATE_CHANNEL_ID:
            await ctx.send("Cette commande ne peut être utilisée que dans le fil dédié.")
            return

        quiz_role_mention = f"<@&{QUIZ_ROLE_ID}>"
        embed = discord.Embed(
            title="📢 Mise à jour du Bot Quiz Cinéma",
            description="De nouvelles fonctionnalités viennent d’arriver pour améliorer votre expérience ! 🎬🍿",
            color=0x1ABC9C
        )
        embed.add_field(
            name="📅 10 questions le dimanche",
            value="Le quiz quotidien propose 10 questions le dimanche, pour pimenter la fin de semaine !",
            inline=False
        )
        embed.add_field(
            name="♻️ Pas de répétition de questions",
            value="Les questions déjà posées ne reviendront pas avant d’avoir épuisé tout le stock.",
            inline=False
        )
        embed.add_field(
            name="📊 Commande `!sr alltime` & `!sr all time`",
            value="Affiche le classement global de tous les temps. `!sr` reste le classement hebdomadaire.",
            inline=False
        )
        embed.add_field(
            name="🚮 Suppression de questions par vote",
            value=(
                "Un nouvel emoji 🚮 a été ajouté sur chaque question.\n"
                "Après 5 votes utilisateurs, la question est supprimée de la base."
            ),
            inline=False
        )
        embed.add_field(
            name="📌 Rappel des commandes clés",
            value=(
                "`!q` - Question aléatoire\n"
                "`!sp` - Tes statistiques\n"
                "`!sr` - Classement hebdo\n"
                "`!sr alltime` ou `!sr all time` - Classement global\n"
                "`!propose question | réponse` - Propose ta question"
            ),
            inline=False
        )
        embed.set_footer(text="Amusez-vous bien et merci pour votre participation !")

        await ctx.send(quiz_role_mention)
        await ctx.send(embed=embed)

    @commands.command(name="aide")
    async def help_cmd(self, ctx):
        embed = discord.Embed(
            title="Aide du bot Quiz Cinéma",
            color=discord.Color.green()
        )
        embed.add_field(name="!q", value="Affiche une question cinéma aléatoire.", inline=False)
        embed.add_field(name="!sp", value="Affiche ton profil et tes statistiques.", inline=False)
        embed.add_field(name="!sr", value="Affiche le classement hebdomadaire.", inline=False)
        embed.add_field(
            name="!propose question | réponse",
            value="Propose une nouvelle question (ou utilise le format Q: ... R: ... ou Q : ... R : ...).",
            inline=False
        )
        embed.add_field(
            name="Quiz quotidien",
            value="Réagis avec l’emoji correspondant à ton score sous le message du quiz pour enregistrer tes points.",
            inline=False
        )
        await ctx.send(embed=embed)

    # ──────────────────────── Tâche quotidienne ─────────────────────────
    @tasks.loop(hours=24)
    async def daily_questions(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(VALIDATED_CHANNEL_ID)

        # 0 = Lundi, 6 = Dimanche
        today_weekday = datetime.datetime.now().weekday()
        nb_questions = 10 if today_weekday == 6 else QUESTIONS_PAR_JOUR

        questions = await dbh.get_unused_questions(self.bot.db)
        if len(questions) < nb_questions:
            await dbh.reset_used_questions(self.bot.db)
            questions = await dbh.get_unused_questions(self.bot.db)

        if len(questions) < nb_questions:
            await channel.send(f"Pas assez de questions pour le quiz du jour ({nb_questions} nécessaires) !")
            return

        day = await dbh.get_day_count(self.bot.db) + 1
        await dbh.set_day_count(self.bot.db, day)

        intro_msg = await dbh.get_jour_message(self.bot.db, day)
        await channel.send(intro_msg)

        selected = random.sample(questions, nb_questions)
        await dbh.mark_questions_used(self.bot.db, [q['id'] for q in selected])

        for q in selected:
            msg = await channel.send(f"**Question :** {q['question']}\n||{q['answer']}||")
            await msg.add_reaction('✅')
            await msg.add_reaction('❌')
            await msg.add_reaction('🚮')
            await asyncio.sleep(2)

        msg = await channel.send(f"<@&{QUIZ_ROLE_ID}> Indiquez votre score du jour en réagissant ci-dessous :")
        score_emojis = (
            ['0️⃣','1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']
            if today_weekday == 6
            else ['0️⃣','1️⃣','2️⃣','3️⃣','4️⃣','5️⃣']
        )
        for emoji in score_emojis:
            await msg.add_reaction(emoji)

    @daily_questions.before_loop
    async def before_daily_questions(self):
        now = datetime.datetime.now()
        target = now.replace(hour=HOUR_QUESTIONS_DAILY,
                             minute=MINUTE_QUESTIONS_DAILY,
                             second=0, microsecond=0)
        if target < now:
            target += datetime.timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        print(f"[DEBUG] Attente de {wait_seconds:.0f} secondes avant le prochain quiz quotidien ({target})")
        await asyncio.sleep(wait_seconds)

# ── export ────────────────────────────────────────────────────────────────────
async def setup(bot):
    # Empêche un double ajout si reload/bug réseau
    if bot.get_cog("QuizCog") is None:
        from commands.quiz_cog import QuizCog  # si défini plus haut c'est déjà importé
        await bot.add_cog(QuizCog(bot))
