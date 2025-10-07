import discord
from discord.ext import commands
from config.settings import UPDATE_CHANNEL_ID, QUIZ_ROLE_ID

class AnnounceCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="annonce_nouveautes")
    async def annonce_nouveautes(self, ctx: commands.Context):
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
            value="Un emoji 🚮 est disponible sur chaque question. Après 3 votes, la question est supprimée.",
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

async def setup(bot):
    if bot.get_cog("AnnounceCmd") is None:
        await bot.add_cog(AnnounceCmd(bot))
