import asyncio
from discord.ext import commands
from helper_functions.questions import pick_random_questions, is_correct, get_current_day
from helper_functions.scores import award_attempt
from helper_functions.embeds import question_embed, result_embed
from helper_functions.logging import log_command

class QuizCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="q")
    @log_command
    async def random_question(self, ctx):
        if ctx.channel.id != self.bot.cfg.COMMANDS_CHANNEL_ID:
            return
        qs = await pick_random_questions(self.bot.db, 1)
        if not qs:
            return await ctx.send("Aucune question disponible.")
        q = qs[0]
        await ctx.send(embed=question_embed(q))

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            return await ctx.send("⏰ Temps écoulé.")

        ok = is_correct(msg.content, q["answer"])
        day = await get_current_day(self.bot.db)
        await award_attempt(self.bot.db, ctx.author.id, day, ok)
        await ctx.send(embed=result_embed(ok, q["answer"]))
