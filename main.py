import discord
from discord.ext import commands, tasks
import json
import random
import os
import asyncio
import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if DISCORD_TOKEN:
    DISCORD_TOKEN = DISCORD_TOKEN.strip('\'" ')
print("DISCORD_TOKEN:", repr(DISCORD_TOKEN))
bot.run(DISCORD_TOKEN)

QUESTIONS_FILE = 'questions.json'
DAILY_SCORES_FILE = 'scores_daily.json'
DAY_COUNT_FILE = 'day_count.json'
MESSAGES_JOUR_FILE = 'messages_jour.json'

PROPOSAL_CHANNEL_ID = os.getenv("PROPOSAL_CHANNEL_ID")
VALIDATED_CHANNEL_ID = os.getenv("VALIDATED_CHANNEL_ID")
COMMANDS_CHANNEL_ID = os.getenv("COMMANDS_CHANNEL_ID")
bot.run(PROPOSAL_CHANNEL_ID, VALIDATED_CHANNEL_ID, COMMANDS_CHANNEL_ID)

HOUR_QUESTIONS_DAILY = 19
MINUTE_QUESTIONS_DAILY = 42

CHECKS_REQUIRED = 1  # Nombre de ✅ requis pour valider

# Date de départ du quiz (à adapter si besoin)
QUIZ_START_DATE = datetime.date(2025, 7, 9)  # Mettre la date de lancement du quiz

def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return default
            return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return default

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_questions():
    return load_json(QUESTIONS_FILE, [])

def save_questions(questions):
    save_json(QUESTIONS_FILE, questions)

def load_daily_scores():
    return load_json(DAILY_SCORES_FILE, {})

def save_daily_scores(scores):
    save_json(DAILY_SCORES_FILE, scores)

def load_day_count():
    return load_json(DAY_COUNT_FILE, {"day": 0})

def save_day_count(day_count):
    save_json(DAY_COUNT_FILE, day_count)

def load_messages_jour():
    return load_json(MESSAGES_JOUR_FILE, {
        "default": "🎬 Jour {day} du quiz cinéma !"
    })

def get_jour_message(day):
    messages = load_messages_jour()
    msg = messages.get("default", "Jour {day} !").replace("{day}", str(day))
    fun = ""
    if str(day) in messages:
        fun = messages[str(day)]
    elif day % 100 == 0 and "multiple_100" in messages:
        fun = messages["multiple_100"].replace("{day}", str(day))
    return msg + ("\n" + fun if fun else "")

def seconds_until(hour, minute=0):
    now = datetime.datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target < now:
        target += datetime.timedelta(days=1)
    return (target - now).total_seconds()

def day_to_date(day_num):
    # Convertit le numéro du jour en date réelle
    return QUIZ_START_DATE + datetime.timedelta(days=day_num-1)

def is_spoiler(text):
    return text.startswith("||") and text.endswith("||")

@bot.command()
async def propose(ctx, *, question_et_reponse: str):
    if ctx.channel.id != PROPOSAL_CHANNEL_ID:
        await ctx.send("Vous devez proposer les questions dans le salon approprié.")
        return
    if "|" not in question_et_reponse:
        await ctx.send("Format attendu : question | réponse")
        return
    question, reponse = [part.strip() for part in question_et_reponse.split("|", 1)]
    msg = await ctx.send(f"Proposition de question : {question}\nRéponse : ||{reponse}||\n\nAjoutez ✅ pour valider !")
    await msg.add_reaction('✅')

@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user}')
    if not daily_questions.is_running():
        daily_questions.start()

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    # Validation des propositions
    if str(reaction.emoji) == '✅':
        if await check_reactions(reaction.message):
            content = reaction.message.content
            if "Proposition de question :" in content and "Réponse :" in content:
                question = content.split("Proposition de question :")[1].split("\n")[0].strip()
                reponse = content.split("Réponse :")[1].split("||")[1].strip()
                questions = load_questions()
                if not any(q['question'] == question for q in questions):
                    questions.append({'question': question, 'answer': reponse})
                    save_questions(questions)
                    validated_channel = bot.get_channel(VALIDATED_CHANNEL_ID)
                    if validated_channel:
                        await validated_channel.send(f"Question validée : {question}\nRéponse : ||{reponse}||")
                    await reaction.message.channel.send("Question ajoutée à la base de données !")
                else:
                    await reaction.message.channel.send("Cette question existe déjà dans la base de données.")

    # Comptage des points UNIQUEMENT pour les questions du quiz quotidien
    if reaction.message.author == bot.user and str(reaction.emoji) in ['✅', '❌']:
        day_count = load_day_count()
        day = str(day_count.get("day", 0))
        scores = load_daily_scores()
        user_id = str(user.id)
        if user_id not in scores:
            scores[user_id] = {}
        if day not in scores[user_id]:
            scores[user_id][day] = {"answered": 0, "score": 0, "msg_ids": []}
        # Empêche double réponse à la même question
        if reaction.message.id in scores[user_id][day]["msg_ids"]:
            return
        scores[user_id][day]["answered"] += 1
        if str(reaction.emoji) == '✅':
            scores[user_id][day]["score"] += 1
        scores[user_id][day]["msg_ids"].append(reaction.message.id)
        save_daily_scores(scores)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == PROPOSAL_CHANNEL_ID:
        content = message.content.strip()
        if content.startswith("Q:") and "R:" in content:
            try:
                question = content.split("Q:")[1].split("R:")[0].strip()
                reponse = content.split("R:")[1].strip()
                # Vérifie que la réponse est bien en spoiler
                if not is_spoiler(reponse):
                    await message.channel.send(
                        f"❌ Merci de mettre la réponse en spoiler Discord, par exemple : `R: ||ma réponse||`"
                    )
                    return
                await message.add_reaction('✅')
            except Exception:
                pass

    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    if reaction.message.channel.id == PROPOSAL_CHANNEL_ID and str(reaction.emoji) == '✅':
        if reaction.count >= CHECKS_REQUIRED:
            content = reaction.message.content
            if content.startswith("Q:") and "R:" in content:
                question = content.split("Q:")[1].split("R:")[0].strip()
                reponse = content.split("R:")[1].strip()
                # Vérifie que la réponse est bien en spoiler
                if not is_spoiler(reponse):
                    await reaction.message.channel.send(
                        f"❌ Merci de mettre la réponse en spoiler Discord, par exemple : `R: ||ma réponse||`"
                    )
                    return
                # Ajoute un ? si besoin
                if not question.endswith("?"):
                    question += " ?"
                questions = load_questions()
                if not any(q['question'] == question for q in questions):
                    # Retire les || pour stocker la réponse sans spoiler
                    answer_text = reponse[2:-2].strip()
                    questions.append({'question': question, 'answer': answer_text})
                    save_questions(questions)
                    await reaction.message.channel.send(
                        f"✅ Nouvelle question ajoutée à la base !\n**Q:** {question}\n**R:** ||{answer_text}||"
                    )
                else:
                    await reaction.message.channel.send("Cette question existe déjà dans la base de données.")

@bot.command()
async def q(ctx):
    """Envoie une question aléatoire avec la réponse cachée, et ajoute les réactions de score."""
    if ctx.channel.id != COMMANDS_CHANNEL_ID:
        await ctx.send("Cette commande n'est autorisée que dans le salon de commandes.")
        return
    questions = load_questions()
    if not questions:
        await ctx.send("Aucune question disponible.")
        return
    question = random.choice(questions)
    msg = await ctx.send(f"**Question :** {question['question']}\n||{question['answer']}||")
    await msg.add_reaction('✅')
    await msg.add_reaction('❌')

@bot.command()
async def sp(ctx):
    scores = load_daily_scores()
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

@bot.command()
async def sr(ctx):
    scores = load_daily_scores()
    now = datetime.datetime.now()
    leaderboard = []
    for user_id, days in scores.items():
        weekly = 0
        for day_str, data in days.items():
            day_num = int(day_str)
            day_date = day_to_date(day_num)
            if day_date.isocalendar()[1] == now.isocalendar()[1] and day_date.year == now.year:
                weekly += data["score"]
        leaderboard.append((user_id, weekly))
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    embed = discord.Embed(
        title="🏆 Classement Weekly 🏆",
        color=discord.Color.gold()
    )
    classement = ""
    for i, (uid, score) in enumerate(leaderboard[:20], 1):
        try:
            user = await bot.fetch_user(int(uid))
            name = user.name
        except Exception:
            name = f"Utilisateur {uid}"
        classement += f"**{i}**. {name} — **{score}**\n"  # tout sur la même ligne
    embed.description = classement
    user_id = str(ctx.author.id)
    user_rank = next((i+1 for i, v in enumerate(leaderboard) if v[0] == user_id), None)
    user_score = next((v[1] for v in leaderboard if v[0] == user_id), 0)
    if user_rank:
        embed.set_footer(text=f"{ctx.author.name} est classé #{user_rank} avec {user_score} points !")
    await ctx.send(embed=embed)

async def check_reactions(message):
    for reaction in message.reactions:
        if str(reaction.emoji) == '✅' and reaction.count >= 5:
            return True
    return False

@tasks.loop(hours=24)
async def daily_questions():
    await bot.wait_until_ready()
    channel = bot.get_channel(VALIDATED_CHANNEL_ID)
    questions = load_questions()
    if len(questions) < 5:
        await channel.send("Pas assez de questions pour le quiz du jour !")
        return
    day_count = load_day_count()
    day_count["day"] += 1
    day = day_count["day"]
    save_day_count(day_count)
    intro_msg = get_jour_message(day)
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
    await asyncio.sleep(seconds_until(HOUR_QUESTIONS_DAILY, MINUTE_QUESTIONS_DAILY))

bot.run(DISCORD_TOKEN)
