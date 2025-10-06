
import datetime
import discord
from discord.ext import commands
from helper_functions.quiz_repo import QuizRepo

class RankingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repo = QuizRepo(bot.db, bot.cfg.QUIZ_START_DATE)

    @commands.command(name="sr")
    async def classement(self, ctx: commands.Context, *, mode: str = "weekly"):
        now = datetime.datetime.now()
        embed = discord.Embed()
        leaderboard = {}
        async with self.bot.db.acquire() as conn:
            rows = await conn.fetch("SELECT user_id, day, score FROM scores_daily")

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
                day_date = self.bot.cfg.QUIZ_START_DATE + datetime.timedelta(days=row["day"] - 1)
                if day_date.isocalendar()[1] == current_week and day_date.year == current_year:
                    uid = str(row["user_id"])
                    leaderboard[uid] = leaderboard.get(uid, 0) + row["score"]
            embed.title = "🏆 Classement Weekly 🏆"
            embed.color = discord.Color.gold()

        sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
        classement = ""
        for i, (uid, score) in enumerate(sorted_lb[:20], 1):
            try:
                user = await self.bot.fetch_user(int(uid))
                name = user.name
            except Exception:
                name = f"Utilisateur {uid}"
            classement += f"**{i}**. {name} — **{score} points**\n"

        embed.description = classement

        user_id = str(ctx.author.id)
        user_rank = next((i+1 for i, v in enumerate(sorted_lb) if v[0] == user_id), None)
        user_score = leaderboard.get(user_id, 0)

        if user_rank:
            suffix = "au total" if mode_clean == "alltime" else "cette semaine"
            embed.set_footer(text=f"{ctx.author.name} est classé #{user_rank} {suffix} avec {user_score} points.")

        await ctx.send(embed=embed)
