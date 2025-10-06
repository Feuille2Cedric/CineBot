import asyncio
from datetime import datetime, timedelta, time as dtime
from discord.ext import tasks
from helper_functions.questions import pick_random_questions, get_current_day
from helper_functions.embeds import question_embed
from helper_functions.scores import award_attempt

class QuizScheduler:
    def __init__(self, bot):
        self.bot = bot

    def start(self):
        self.daily_quiz_task.start()

    def cog_unload(self):
        self.daily_quiz_task.cancel()

    @tasks.loop(minutes=1)
    async def daily_quiz_task(self):
        cfg = self.bot.cfg
        now = datetime.now()
        target = now.replace(hour=cfg.HOUR_QUESTIONS_DAILY, minute=cfg.MINUTE_QUESTIONS_DAILY, second=0, microsecond=0)
        if now >= target and (now - target) < timedelta(minutes=1):
            channel = self.bot.get_channel(cfg.COMMANDS_CHANNEL_ID)
            if not channel:
                return
            qs = await pick_random_questions(self.bot.db, 5)
            for q in qs:
                await channel.send(embed=question_embed(q))
                # Passive mode (no auto collection here), interactive logic remains in commands
                await asyncio.sleep(2)
