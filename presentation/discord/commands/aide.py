import discord
from discord.ext import commands

class HelpCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="aide")
    async def help_cmd(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Aide du bot Quiz Cinéma",
            color=discord.Color.green()
        )
        embed.add_field(name="!q", value="Affiche une question cinéma aléatoire.", inline=False)
        embed.add_field(name="!sp", value="Affiche ton profil et tes statistiques.", inline=False)
        embed.add_field(name="!sr", value="Affiche le classement hebdomadaire.", inline=False)
        embed.add_field(
            name="!propose question | réponse",
            value="Propose une nouvelle question (ou format `Q: ... R: ...`).",
            inline=False
        )
        embed.add_field(
            name="Quiz quotidien",
            value="Réagis avec l’emoji correspondant à ton score sous le message du quiz pour l’enregistrer.",
            inline=False
        )
        await ctx.send(embed=embed)

async def setup(bot):
    if bot.get_cog("HelpCmd") is None:
        await bot.add_cog(HelpCmd(bot))
