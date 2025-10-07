from discord.ext import commands
from config.settings import PROPOSAL_CHANNEL_ID
from app.use_cases.questions import parse_q_r, is_spoiler

class ProposeCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="propose")
    async def propose(self, ctx: commands.Context, *, question_et_reponse: str):
        if ctx.channel.id != PROPOSAL_CHANNEL_ID:
            await ctx.send("Vous devez proposer les questions dans le salon approprié.")
            return
        q, r = parse_q_r(question_et_reponse)
        if not (q and r):
            await ctx.send("Format attendu : `Q: ... R: ...` ou `question | réponse`.")
            return
        if not is_spoiler(r):
            r = f"||{r}||"
        msg = await ctx.send(f"Proposition de question : {q}\nRéponse : {r}\n\nAjoutez ✅ pour valider !")
        await msg.add_reaction('✅')

async def setup(bot):
    if bot.get_cog("ProposeCmd") is None:
        await bot.add_cog(ProposeCmd(bot))
