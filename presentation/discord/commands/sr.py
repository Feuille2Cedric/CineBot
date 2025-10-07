import discord
import datetime
from discord.ext import commands
from app.domain.repositories import ScoreRepo
from app.domain.models import day_to_date
from config.settings import QUIZ_START_DATE

class SRCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.srepo: ScoreRepo = bot.repos["scores"]

    @commands.command(name="sr")
    async def sr(self, ctx: commands.Context, *, mode: str = "weekly"):
        now = datetime.datetime.now()
        rows = await self.srepo.fetch_rows()

        leaderboard = {}
        mode_clean = mode.lower().replace(" ", "")
        if mode_clean == "alltime" or mode_clean == "all time":
            title = "🏅 Classement Global – Tous Temps"
            color = discord.Color.purple()
            for row in rows:
                uid = str(row["user_id"])
                leaderboard[uid] = leaderboard.get(uid, 0) + row["score"]
        else:
            title = "🏆 Classement Weekly 🏆"
            color = discord.Color.gold()
            current_week, current_year = now.isocalendar()[1], now.year
            for row in rows:
                ddate = day_to_date(QUIZ_START_DATE, row["day"])
                if ddate.isocalendar()[1] == current_week and ddate.year == current_year:
                    uid = str(row["user_id"])
                    leaderboard[uid] = leaderboard.get(uid, 0) + row["score"]

        sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
        desc = ""
        for i, (uid, score) in enumerate(sorted_lb[:20], 1):
            try:
                user = await self.bot.fetch_user(int(uid))
                name = user.name
            except Exception:
                name = f"Utilisateur {uid}"
            desc += f"**{i}**. {name} — **{score} points**\n"

        embed = discord.Embed(title=title, description=desc, color=color)
        user_id = str(ctx.author.id)
        user_rank = next((i+1 for i, v in enumerate(sorted_lb) if v[0] == user_id), None)
        user_score = leaderboard.get(user_id, 0)
        if user_rank:
            suffix = "au total" if mode_clean == "alltime" else "cette semaine"
            embed.set_footer(text=f"{ctx.author.name} est classé #{user_rank} {suffix} avec {user_score} points.")
        await ctx.send(embed=embed)

async def setup(bot):
    if bot.get_cog("SRCmd") is None:
        await bot.add_cog(SRCmd(bot))
