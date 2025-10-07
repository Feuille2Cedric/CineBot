import asyncio
from presentation.discord.bot import create_bot
from config.settings import DISCORD_TOKEN

async def main():
    # Création et initialisation du bot (DB, Cogs, etc.)
    bot = await create_bot()

    # Démarrage du bot Discord
    print("[BOOT] Démarrage du bot Quiz Cinéma...")
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] Arrêt manuel du bot.")
