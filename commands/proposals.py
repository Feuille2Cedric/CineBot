import re
import asyncio
from discord.ext import commands
from helper_functions.db import fetchrow, execute, fetch
from helper_functions.logging import log_command

PROPOSE_CMD_REGEX = re.compile(r"^\s*!propose\s+(.+?)\s*\|\s*(.+)\s*$", re.IGNORECASE | re.DOTALL)
QR_FREEFORM_Q = re.compile(r"^\s*Q\s*:\s*(.+)$", re.IGNORECASE)
QR_FREEFORM_A = re.compile(r"^\s*R\s*:\s*\|{0,2}(.+?)\|{0,2}\s*$", re.IGNORECASE)

class ProposalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _parse_proposal(self, content: str) -> tuple[str, str] | None:
        m = PROPOSE_CMD_REGEX.match(content)
        if m:
            return m.group(1).strip(), m.group(2).strip()
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        if len(lines) >= 2:
            mq = QR_FREEFORM_Q.match(lines[0])
            ma = QR_FREEFORM_A.match(lines[1])
            if mq and ma:
                return mq.group(1).strip(), ma.group(1).strip()
        return None

    async def _post_to_validated(self, question: str, answer: str):
        ch = self.bot.get_channel(self.bot.cfg.VALIDATED_CHANNEL_ID)
        if ch:
            await ch.send(f"✅ Question validée:\nQ: {question}\nR: ||{answer}||")

    @commands.command(name="propose")
    @log_command
    async def propose_command(self, ctx, *, payload: str = ""):
        # Only allowed in proposal channel
        if ctx.channel.id != self.bot.cfg.PROPOSAL_CHANNEL_ID:
            return
        parsed = self._parse_proposal(ctx.message.content)
        if not parsed:
            return await ctx.send("Format attendu: !propose Question ? | Réponse  OU  Ligne 1: Q: question  /  Ligne 2: R: ||réponse||")
        q, a = parsed

        # Preview for voters
        msg = await ctx.send(f"Proposition de <@{ctx.author.id}>:\nQ: {q}\nR: ||{a}||\nValider avec ✅")
        await msg.add_reaction("✅")

        checks_required = self.bot.cfg.CHECKS_REQUIRED

        def check(reaction, user):
            return (
                reaction.message.id == msg.id
                and str(reaction.emoji) == "✅"
                and not user.bot
            )

        approved_by = set()
        try:
            while len(approved_by) < checks_required:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=3600, check=check)
                approved_by.add(user.id)
        except asyncio.TimeoutError:
            return await ctx.send("Validation expirée.")

        # Insert into existing table questions (no schema change)
        await execute(self.bot.db,
            "INSERT INTO questions (question, answer) VALUES ($1, $2)", q, a
        )
        await self._post_to_validated(q, a)
        await ctx.send("Question ajoutée à la base ✅")
