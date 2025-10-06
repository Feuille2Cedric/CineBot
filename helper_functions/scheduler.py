
import random
import asyncio
import datetime
from discord.ext import tasks
import discord

from .config import Config
from .quiz_repo import QuizRepo

class QuizScheduler:
    def __init__(self, bot):
        self.bot = bot
        self.cfg: Config = bot.cfg
        self.repo = QuizRepo(bot.db, self.cfg.QUIZ_START_DATE)
        self.loop_task.change_interval(hours=24)

    def start(self):
        if not self.loop_task.is_running():
            self.loop_task.start()

    @tasks.loop(hours=24)
    async def loop_task(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(self.cfg.VALIDATED_CHANNEL_ID)

        today_weekday = datetime.datetime.now().weekday()  # 0 = Lundi ; 6 = Dimanche
        nb_questions = 10 if today_weekday == 6 else self.cfg.QUESTIONS_PAR_JOUR

        questions = await self.repo.get_unused_questions()
        if len(questions) < nb_questions:
            await self.repo.reset_used_questions()
            questions = await self.repo.get_unused_questions()

        if len(questions) < nb_questions:
            await channel.send(f"Pas assez de questions pour le quiz du jour ({nb_questions} nécessaires) !")
            return

        day = await self.repo.get_day_count() + 1
        await self.repo.set_day_count(day)

        intro_msg = await self.repo.get_jour_message(day)
        await channel.send(intro_msg)

        selected = random.sample(questions, nb_questions)
        await self.repo.mark_questions_used([q['id'] for q in selected])

        for q in selected:
            msg = await channel.send(f"**Question :** {q['question']}\n||{q['answer']}||")
            await msg.add_reaction('✅')
            await msg.add_reaction('❌')
            await msg.add_reaction('🚮')
            await asyncio.sleep(2)

        quiz_role_mention = f"<@&{self.cfg.QUIZ_ROLE_ID}>"
        prompt_msg = await channel.send(f"{quiz_role_mention} Indiquez votre score du jour en réagissant ci-dessous :")

        if today_weekday == 6:
            score_emojis = ['0️⃣','1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']
        else:
            score_emojis = ['0️⃣','1️⃣','2️⃣','3️⃣','4️⃣','5️⃣']

        for e in score_emojis:
            await prompt_msg.add_reaction(e)

    @loop_task.before_loop
    async def before_loop(self):
        now = datetime.datetime.now()
        target = now.replace(hour=self.cfg.HOUR_QUESTIONS_DAILY, minute=self.cfg.MINUTE_QUESTIONS_DAILY, second=0, microsecond=0)
        if target < now:
            target += datetime.timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())
