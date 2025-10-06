
import datetime
import discord
from discord.ext import commands
from helper_functions.quiz_repo import QuizRepo

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repo = QuizRepo(bot.db, bot.cfg.QUIZ_START_DATE)

    @commands.command(name="sp")
    async def stats_perso(self, ctx: commands.Context):
        scores = await self.repo.get_scores()
        user_id = str(ctx.author.id)
        now = datetime.datetime.now()

        daily = weekly = monthly = total = correct = total_questions = 0
        for day_str, data in scores.get(user_id, {}).items():
            day_num = int(day_str)
            day_date = self.repo.day_to_date(day_num)
            if day_date == now.date():
                daily += data["score"]
            if day_date.isocalendar()[1] == now.isocalendar()[1] and day_date.year == now.year:
                weekly += data["score"]
            if day_date.month == now.month and day_date.year == now.year:
                monthly += data["score"]
            total += data["score"]
            correct += data["score"]
            total_questions += self.bot.cfg.QUESTIONS_PAR_JOUR

        precision = (correct / total_questions * 100) if total_questions else 0
        leaderboard = []
        for uid, days in scores.items():
            t = sum(d["score"] for d in days.values())
            leaderboard.append((uid, t))
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        rank = next((i+1 for i, v in enumerate(leaderboard) if v[0] == user_id), None)

        embed = discord.Embed(title=f"Profil de {ctx.author.name} 📊", color=discord.Color.blue())
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
