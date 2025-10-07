import discord
from discord.ext import commands
from app.use_cases.scoring import compute_user_stats

class SPCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.srepo = bot.repos["scores"]

    @commands.command(name="sp")
    async def sp(self, ctx: commands.Context):
        stats = await compute_user_stats(self.srepo, ctx.author.id)
        embed = discord.Embed(
            title=f"Profil de {ctx.author.name} 📊",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="📅 Score quotidien", value=f"{stats['daily']} points", inline=False)
        embed.add_field(name="📆 Score hebdomadaire", value=f"{stats['weekly']} points", inline=False)
        embed.add_field(name="🗓️ Score mensuel", value=f"{stats['monthly']} points", inline=False)
        embed.add_field(name="🏆 Score total", value=f"{stats['total']} points", inline=False)
        embed.add_field(name="🎯 Précision", value=f"{stats['precision']:.2f}%", inline=False)
        embed.add_field(name="💯 Total de questions répondues", value=f"{stats['total_questions']} questions", inline=False)
        if stats['rank']:
            embed.set_footer(text=f"Tu es classé #{stats['rank']} total avec {stats['total']} points !")
        await ctx.send(embed=embed)

async def setup(bot):
    if bot.get_cog("SPCmd") is None:
        await bot.add_cog(SPCmd(bot))
