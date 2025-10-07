import asyncio
import datetime
from discord.ext import commands, tasks
from config.settings import (
    VALIDATED_CHANNEL_ID, QUIZ_ROLE_ID,
    HOUR_QUESTIONS_DAILY, MINUTE_QUESTIONS_DAILY
)
from app.use_cases.daily_quiz import pick_daily_ids
from app.use_cases.day_counter import next_day
from app.domain.repositories import QuestionRepo, DayCounterRepo, DailyMessageRepo

class SchedulerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.qrepo: QuestionRepo = bot.repos["questions"]
        self.drepo: DayCounterRepo = bot.repos["days"]
        self.mrepo: DailyMessageRepo = bot.repos["daily_msg"]
        if not self.daily.is_running():
            self.daily.start()

    @tasks.loop(hours=24)
    async def daily(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(VALIDATED_CHANNEL_ID)
        if not channel:
            print("[WARN] VALIDATED_CHANNEL_ID introuvable.")
            return

        weekday = datetime.datetime.now().weekday()  # 0..6
        ids = await pick_daily_ids(self.qrepo, weekday)
        if not ids:
            await channel.send("Pas assez de questions pour le quiz du jour !")
            return

        day = await next_day(self.drepo)
        intro_msg = await self.mrepo.get_by_day(day)
        await channel.send(intro_msg)

        questions = await self.qrepo.get_by_ids(ids)
        for q in questions:
            msg = await channel.send(f"**Question :** {q.question}\n||{q.answer}||")
            for e in ('✅', '❌', '🚮'):
                await msg.add_reaction(e)
            await asyncio.sleep(2)

        msg = await channel.send(f"<@&{QUIZ_ROLE_ID}> Indiquez votre score du jour en réagissant ci-dessous :")
        score_emojis = (
            ['0️⃣','1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']
            if weekday == 6 else ['0️⃣','1️⃣','2️⃣','3️⃣','4️⃣','5️⃣']
        )
        for e in score_emojis:
            await msg.add_reaction(e)

    @daily.before_loop
    async def before_daily(self):
        now = datetime.datetime.now()
        target = now.replace(hour=HOUR_QUESTIONS_DAILY, minute=MINUTE_QUESTIONS_DAILY, second=0, microsecond=0)
        if target < now:
            target += datetime.timedelta(days=1)
        wait = (target - now).total_seconds()
        print(f"[DEBUG] Daily quiz dans {wait:.0f}s (target={target})")
        await asyncio.sleep(wait)

async def setup(bot: commands.Bot):
    if bot.get_cog("SchedulerCog") is None:
        await bot.add_cog(SchedulerCog(bot))
