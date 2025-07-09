import discord
from discord.ext import commands, tasks
import asyncpg
import os
import random
import asyncio
import datetime
import json

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATABASE_URL = os.getenv("DATABASE_URL")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PROPOSAL_CHANNEL_ID = int(os.getenv("PROPOSAL_CHANNEL_ID"))
VALIDATED_CHANNEL_ID = int(os.getenv("VALIDATED_CHANNEL_ID"))
COMMANDS_CHANNEL_ID = int(os.getenv("COMMANDS_CHANNEL_ID"))

HOUR_QUESTIONS_DAILY = int(os.getenv("HOUR_QUESTIONS_DAILY"))
MINUTE_QUESTIONS_DAILY = int(os.getenv("MINUTE_QUESTIONS_DAILY"))
CHECKS_REQUIRED = int(os.getenv("CHECKS_REQUIRED"))
QUIZ_START_DATE = datetime.date(2025, 7, 9)

# --- Fonctions BDD ---
@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user}')
    bot.db = await asyncpg.create_pool(DATABASE_URL)
    # Création auto des tables si besoin
    await bot.db.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id SERIAL PRIMARY KEY,
        question TEXT NOT NULL,
        answer TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS scores_daily (
        user_id BIGINT NOT NULL,
        day INTEGER NOT NULL,
        answered INTEGER DEFAULT 0,
        score INTEGER DEFAULT 0,
        msg_ids TEXT DEFAULT '[]',
        PRIMARY KEY (user_id, day)
    );
    CREATE TABLE IF NOT EXISTS day_count (
        id SERIAL PRIMARY KEY,
        day INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS messages_jour (
        day INTEGER PRIMARY KEY,
        message TEXT NOT NULL
    );
    """)
    if not daily_questions.is_running():
        daily_questions.start()

def is_spoiler(text):
    return text.startswith("||") and text.endswith("||")

async def get_questions():
    return await bot.db.fetch("SELECT id, question, answer FROM questions")

async def save_question(question, answer):
    await bot.db.execute(
        "INSERT INTO questions (question, answer) VALUES ($1, $2) ON CONFLICT DO NOTHING", question, answer
    )

async def get_random_question():
    return await bot.db.fetchrow("SELECT question, answer FROM questions ORDER BY random() LIMIT 1")

async def get_day_count():
    row = await bot.db.fetchrow("SELECT day FROM day_count ORDER BY id DESC LIMIT 1")
    return row['day'] if row else 0

async def set_day_count(day):
    await bot.db.execute("INSERT INTO day_count(day) VALUES($1)", day)

async def get_jour_message(day):
    row = await bot.db.fetchrow("SELECT message FROM messages_jour WHERE day=$1", day)
    if row:
        return row['message']
    return f"🎬 Jour {day} du quiz cinéma !"

async def get_scores():
    rows = await bot.db.fetch("SELECT * FROM scores_daily")
    # On retourne sous forme de dict imbriqué comme avant
    scores = {}
    for row in rows:
        uid = str(row['user_id'])
        day = str(row['day'])
        if uid not in scores:
            scores[uid] = {}
        scores[uid][day] = {
            "answered": row['answered'],
            "score": row['score'],
            "msg_ids": json.loads(row['msg_ids'])
        }
    return scores

async def save_score(user_id, day, answered, score, msg_ids):
    await bot.db.execute("""
        INSERT INTO scores_daily (user_id, day, answered, score, msg_ids)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (user_id, day) DO UPDATE
        SET answered=$3, score=$4, msg_ids=$5
    """, int(user_id), int(day), answered, score, json.dumps(msg_ids))

def day_to_date(day_num):
    return QUIZ_START_DATE + datetime.timedelta(days=day_num-1)

# --- Commandes et events adaptés ---
@bot.command()
async def propose(ctx, *, question_et_reponse: str):
    if ctx.channel.id != PROPOSAL_CHANNEL_ID:
        await ctx.send("Vous devez proposer les questions dans le salon approprié.")
        return
    if "|" not in question_et_reponse:
        await ctx.send("Format attendu : question | réponse")
        return
    question, reponse = [part.strip() for part in question_et_reponse.split("|", 1)]
    await save_question(question, reponse)
    await ctx.send(f"Proposition de question ajoutée : {question}\nRéponse : ||{reponse}||")

@bot.command()
async def q(ctx):
    if ctx.channel.id != COMMANDS_CHANNEL_ID:
        await ctx.send("Cette commande n'est autorisée que dans le salon de commandes.")
        return
    row = await get_random_question()
    if not row:
        await ctx.send("Aucune question disponible.")
        return
    msg = await ctx.send(f"**Question :** {row['question']}\n||{row['answer']}||")
    await msg.add_reaction('✅')
    await msg.add_reaction('❌')

@bot.command()
async def sp(ctx):
    scores = await get_scores()
    user_id = str(ctx.author.id)
    now = datetime.datetime.now()
    daily = weekly = monthly = total = correct = total_questions = 0
    for day_str, data in scores.get(user_id, {}).items():
        day_num = int(day_str)
        day_date = day_to_date(day_num)
        if day_date == now.date():
            daily += data["score"]
        if day_date.isocalendar()[1] == now.isocalendar()[1] and day_date.year == now.year:
            weekly += data["score"]
        if day_date.month == now.month and day_date.year == now.year:
            monthly += data["score"]
        total += data["score"]
        correct += data["score"]
        total_questions += data["answered"]
    precision = (correct / total_questions * 100) if total_questions else 0
    leaderboard = []
    for uid, days in scores.items():
        t = sum(d["score"] for d in days.values())
        leaderboard.append((uid, t))
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    rank = next((i+1 for i, v in enumerate(leaderboard) if v[0] == user_id), None)

    embed = discord.Embed(
        title=f"Profil de {ctx.author.name} 📊",
        color=discord.Color.blue()
    )
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

# ... (adapte les autres commandes/events de la même façon !)

@tasks.loop(hours=24)
async def daily_questions():
    await bot.wait_until_ready()
    channel = bot.get_channel(VALIDATED_CHANNEL_ID)
    questions = await get_questions()
    if len(questions) < 5:
        await channel.send("Pas assez de questions pour le quiz du jour !")
        return
    day = await get_day_count() + 1
    await set_day_count(day)
    intro_msg = await get_jour_message(day)
    await channel.send(intro_msg)
    selected = random.sample(questions, 5)
    for q in selected:
        msg = await channel.send(f"**Question :** {q['question']}\n||{q['answer']}||")
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')
        await asyncio.sleep(2)
    msg = await channel.send("@everyone Indiquez votre score du jour en réagissant ci-dessous :")
    for emoji in ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']:
        await msg.add_reaction(emoji)

@daily_questions.before_loop
async def before_daily_questions():
    now = datetime.datetime.now()
    target = now.replace(hour=HOUR_QUESTIONS_DAILY, minute=MINUTE_QUESTIONS_DAILY, second=0, microsecond=0)
    if target < now:
        target += datetime.timedelta(days=1)
    await asyncio.sleep((target - now).total_seconds())

bot.run(DISCORD_TOKEN)
