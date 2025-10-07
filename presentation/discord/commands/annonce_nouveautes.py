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
            title="📢 **Mise à jour du Bot Quiz Cinéma**",
            description="🎬 **Des nouvelles fonctionnalités arrivent !** 🍿 Le code a été refondu et les devinettes sont maintenant disponibles !",
            color=0x1ABC9C
        )
        embed.add_field(
            name="🎉 **Ajout des Devinettes**",
            value="Vous pouvez maintenant jouer à des **devinettes** sur des films ! 🤔 Chaque question vous demande de choisir parmi des films, et la bonne réponse est cachée en spoiler. 🍿",
            inline=False
        )
        embed.add_field(
            name="🔄 **Refonte du code**",
            value="Le code du bot a été **refondu** pour améliorer l'expérience utilisateur. Des **fonctionnalités plus robustes** et une meilleure gestion des questions ont été intégrées. ⚙️",
            inline=False
        )
        embed.add_field(
            name="📌 **Rappel des commandes clés**",
            value=(  
                "`!q` - Question aléatoire 🎲\n"
                "`!sp` - Tes statistiques 📊\n"
                "`!sr` - Classement hebdo 📅\n"
                "`!sr alltime` ou `!sr all time` - Classement global 🌍\n"
                "`!propose question | réponse` - Propose une nouvelle question ! 📝\n"
                "`!devinette` - Lance une devinette 🎥"
            ),
            inline=False
        )
        embed.set_footer(text="Merci pour votre participation et amusez-vous bien ! 🙌")

        # Envoi du message
        await ctx.send(quiz_role_mention)
        await ctx.send(embed=embed)

async def setup(bot):
    if bot.get_cog("AnnounceCmd") is None:
        await bot.add_cog(AnnounceCmd(bot))
