
import discord
from discord.ext import commands
from helper_functions.quiz_repo import QuizRepo

class QuizCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repo = QuizRepo(bot.db, bot.cfg.QUIZ_START_DATE)

    @commands.command(name="q")
    async def random_question(self, ctx: commands.Context):
        if ctx.channel.id != self.bot.cfg.COMMANDS_CHANNEL_ID:
            await ctx.send("Cette commande n'est autorisée que dans le salon de commandes.")
            return
        row = await self.repo.get_random_question()
        if not row:
            await ctx.send("Aucune question disponible.")
            return
        msg = await ctx.send(f"**Question :** {row['question']}\n||{row['answer']}||")
        for emoji in ('✅','❌','🚮'):
            await msg.add_reaction(emoji)

    @commands.command(name="annonce_nouveautes")
    async def annonce(self, ctx: commands.Context):
        if ctx.channel.id != self.bot.cfg.UPDATE_CHANNEL_ID:
            await ctx.send("Cette commande ne peut être utilisée que dans le fil dédié.")
            return
        quiz_role_mention = quiz_role_mention = f"<@&{self.bot.cfg.QUIZ_ROLE_ID}>"

        embed = discord.Embed(
            title="📢 Mise à jour du Bot Quiz Cinéma",
            description="De nouvelles fonctionnalités viennent d’arriver pour améliorer votre expérience ! 🎬🍿",
            color=0x1ABC9C
        )
        embed.add_field(name="📅 10 questions le dimanche",
                        value="Le quiz quotidien propose 10 questions le dimanche, pour pimenter la fin de semaine !",
                        inline=False)
        embed.add_field(name="♻️ Pas de répétition de questions",
                        value="Les questions déjà posées ne reviendront pas avant d’avoir épuisé tout le stock.",
                        inline=False)
        embed.add_field(name="📊 Commande `!sr alltime` & `!sr all time`",
                        value="Affiche le classement global de tous les temps. `!sr` reste le classement hebdomadaire.",
                        inline=False)
        embed.add_field(name="🚮 Suppression de questions par vote",
                        value=("Un nouvel emoji 🚮 a été ajouté sur chaque question.\n"
                               "Après 5 votes utilisateurs, la question est supprimée de la base."),
                        inline=False)
        embed.add_field(
            name="📌 Rappel des commandes clés",
            value=("`!q` - Question aléatoire\n"
                   "`!sp` - Tes statistiques\n"
                   "`!sr` - Classement hebdo\n"
                   "`!sr alltime` ou `!sr all time` - Classement global\n"
                   "`!propose question | réponse` - Propose ta question"),
            inline=False
        )
        embed.set_footer(text="Amusez-vous bien et merci pour votre participation !")

        await ctx.send(quiz_role_mention)
        await ctx.send(embed=embed)

    @commands.command(name="aide")
    async def aide(self, ctx: commands.Context):
        embed = discord.Embed(title="Aide du bot Quiz Cinéma", color=discord.Color.green())
        embed.add_field(name="!q", value="Affiche une question cinéma aléatoire.", inline=False)
        embed.add_field(name="!sp", value="Affiche ton profil et tes statistiques.", inline=False)
        embed.add_field(name="!sr", value="Affiche le classement hebdomadaire.", inline=False)
        embed.add_field(name="!propose question | réponse",
                        value="Propose une nouvelle question (ou utilise le format Q: ... R: ... ou Q : ... R : ...).",
                        inline=False)
        embed.add_field(name="Quiz quotidien",
                        value="Réagis avec l’emoji correspondant à ton score sous le message du quiz pour enregistrer tes points.",
                        inline=False)
        await ctx.send(embed=embed)
