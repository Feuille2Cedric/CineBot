import discord
from discord.ext import commands, tasks
import asyncpg
import os
import random
import asyncio
import datetime
import json
import re

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATABASE_URL = os.getenv("DATABASE_URL")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PROPOSAL_CHANNEL_ID = int(os.getenv("PROPOSAL_CHANNEL_ID"))
VALIDATED_CHANNEL_ID = int(os.getenv("VALIDATED_CHANNEL_ID"))
COMMANDS_CHANNEL_ID = int(os.getenv("COMMANDS_CHANNEL_ID"))
UPDATE_CHANNEL_ID = int(os.getenv("UPDATE_CHANNEL_ID"))

# Récup brut
raw_quiz_role_id = os.getenv("QUIZ_ROLE_ID", "")
print(f"[DEBUG] Valeur brute QUIZ_ROLE_ID depuis env : '{raw_quiz_role_id}'")

# Nettoyage (supprime espaces + un éventuel '=' au début)
clean_quiz_role_id = raw_quiz_role_id.strip().lstrip("=")
print(f"[DEBUG] Valeur nettoyée QUIZ_ROLE_ID : '{clean_quiz_role_id}'")

# Conversion en int
QUIZ_ROLE_ID = int(clean_quiz_role_id)
print(f"[DEBUG] QUIZ_ROLE_ID en int = {QUIZ_ROLE_ID}")

HOUR_QUESTIONS_DAILY = int(os.getenv("HOUR_QUESTIONS_DAILY"))
MINUTE_QUESTIONS_DAILY = int(os.getenv("MINUTE_QUESTIONS_DAILY"))
CHECKS_REQUIRED = int(os.getenv("CHECKS_REQUIRED"))
QUIZ_START_DATE = datetime.date(2025, 7, 9)

QUESTIONS_PAR_JOUR = 5

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
    CREATE TABLE IF NOT EXISTS used_questions (
        question_id INTEGER PRIMARY KEY
    );
    """)
    if not daily_questions.is_running():
        daily_questions.start()

def is_spoiler(text):
    return text.startswith("||") and text.endswith("||")

def extract_question_reponse(content):
    # Accepte Q: ou Q : et R: ou R :
    match = re.search(r'Q\s*:\s*(.+?)R\s*:\s*(.+)', content, re.DOTALL | re.IGNORECASE)
    if match:
        question = match.group(1).strip()
        reponse = match.group(2).strip()
        return question, reponse
    return None, None

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

async def get_unused_questions():
    return await bot.db.fetch("""
        SELECT id, question, answer
        FROM questions
        WHERE id NOT IN (SELECT question_id FROM used_questions)
    """)

async def mark_questions_used(question_ids):
    for qid in question_ids:
        await bot.db.execute(
            "INSERT INTO used_questions (question_id) VALUES ($1) ON CONFLICT DO NOTHING", qid
        )

async def reset_used_questions():
    await bot.db.execute("TRUNCATE used_questions")

async def get_scores():
    rows = await bot.db.fetch("SELECT * FROM scores_daily")
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
    msg = await ctx.send(f"Proposition de question : {question}\nRéponse : ||{reponse}||\n\nAjoutez ✅ pour valider !")
    await msg.add_reaction('✅')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == PROPOSAL_CHANNEL_ID:
        content = message.content.strip()
        question, reponse = extract_question_reponse(content)
        if question and reponse:
            try:
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

    # --- Suppression de question via 🚮 ---
    if str(reaction.emoji) == '🚮':
        try:
            users = [u async for u in reaction.users() if not u.bot]
            if len(users) >= 6:  # 5 votes utilisateurs + 1 ajout bot
                content = reaction.message.content
                match = re.search(r"\*\*Question :\*\* (.+?)\n\|\|", content, re.DOTALL)
                if match:
                    question_text = match.group(1).strip()
                    await bot.db.execute("DELETE FROM questions WHERE question = $1", question_text)
                    await reaction.message.channel.send(f"🗑️ La question « {question_text} » a été supprimée après signalement.")
        except Exception as e:
            print(f"Erreur suppression via 🚮 : {e}")

    # --- Validation des propositions de questions ---
    if reaction.message.channel.id == PROPOSAL_CHANNEL_ID and str(reaction.emoji) == '✅':
        # On compte le nombre d'utilisateurs uniques (hors bot) ayant mis ✅
        users = [u async for u in reaction.users() if not u.bot]
        if len(users) == CHECKS_REQUIRED:  # Ajout à la 2e validation uniquement
            content = reaction.message.content
            # Cas du format Q: ... R: ... (tous formats)
            question, reponse = extract_question_reponse(content)
            if question and reponse:
                if not is_spoiler(reponse):
                    await reaction.message.channel.send(
                        f"❌ Merci de mettre la réponse en spoiler Discord, par exemple : `R: ||ma réponse||`"
                    )
                    return
                if not question.endswith("?"):
                    question += " ?"
                answer_text = reponse[2:-2].strip()
                rows = await bot.db.fetch("SELECT 1 FROM questions WHERE question = $1", question)
                if not rows:
                    await save_question(question, answer_text)
                    await reaction.message.channel.send(
                        f"✅ Nouvelle question ajoutée à la base !\n**Q:** {question}\n**R:** ||{answer_text}||"
                    )
                else:
                    await reaction.message.channel.send("Cette question existe déjà dans la base de données.")
            # Cas du format "Proposition de question : ... Réponse : ||...||"
            elif "Proposition de question :" in content and "Réponse :" in content:
                question = content.split("Proposition de question :")[1].split("\n")[0].strip()
                reponse = content.split("Réponse :")[1].split("||")[1].strip()
                rows = await bot.db.fetch("SELECT 1 FROM questions WHERE question = $1", question)
                if not rows:
                    await save_question(question, reponse)
                    validated_channel = bot.get_channel(VALIDATED_CHANNEL_ID)
                    if validated_channel:
                        await validated_channel.send(f"Question validée : {question}\nRéponse : ||{reponse}||")
                    await reaction.message.channel.send("Question ajoutée à la base de données !")
                else:
                    await reaction.message.channel.send("Cette question existe déjà dans la base de données.")

    # --- Enregistrement des scores du quiz quotidien ---
    if reaction.message.channel.id == VALIDATED_CHANNEL_ID:
        if reaction.message.content.startswith("@everyone Indiquez votre score"):
            emoji_to_score = {
                '0️⃣': 0,
                '1️⃣': 1,
                '2️⃣': 2,
                '3️⃣': 3,
                '4️⃣': 4,
                '5️⃣': 5,
            }
            if str(reaction.emoji) in emoji_to_score:
                score = emoji_to_score[str(reaction.emoji)]
                day = await get_day_count()
                await save_score(user.id, day, 1, score, [])
                print(f"[DEBUG] Score enregistré : user={user.id}, day={day}, score={score}")

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
    await msg.add_reaction('🚮')

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
        total_questions += QUESTIONS_PAR_JOUR  # On ajoute 5 questions pour chaque jour joué
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
async def sr(ctx, *, mode: str = "weekly"):  # ← astérisque pour capturer toute la chaîne
    now = datetime.datetime.now()
    embed = discord.Embed()
    leaderboard = {}
    rows = await bot.db.fetch("SELECT user_id, day, score FROM scores_daily")

    # normalisation : minuscules + suppression des espaces
    mode_clean = mode.lower().replace(" ", "")

    if mode_clean == "alltime":
        # ------- CLASSEMENT TOUS LES TEMPS -------
        for row in rows:
            uid = str(row["user_id"])
            leaderboard[uid] = leaderboard.get(uid, 0) + row["score"]
        embed.title = "🏅 Classement Global – Tous Temps"
        embed.color = discord.Color.purple()
    else:
        # ------- CLASSEMENT HEBDOMADAIRE -------
        current_week = now.isocalendar()[1]
        current_year = now.year
        for row in rows:
            day_date = QUIZ_START_DATE + datetime.timedelta(days=row["day"] - 1)
            if day_date.isocalendar()[1] == current_week and day_date.year == current_year:
                uid = str(row["user_id"])
                leaderboard[uid] = leaderboard.get(uid, 0) + row["score"]
        embed.title = "🏆 Classement Weekly 🏆"
        embed.color = discord.Color.gold()

    # tri et affichage
    sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    classement = ""
    for i, (uid, score) in enumerate(sorted_lb[:20], 1):
        try:
            user = await bot.fetch_user(int(uid))
            name = user.name
        except Exception:
            name = f"Utilisateur {uid}"
        classement += f"**{i}**. {name} — **{score} points**\n"

    embed.description = classement

    # footer position dans le classement
    user_id = str(ctx.author.id)
    user_rank = next((i+1 for i, v in enumerate(sorted_lb) if v[0] == user_id), None)
    user_score = leaderboard.get(user_id, 0)

    if user_rank:
        suffix = "au total" if mode_clean == "alltime" else "cette semaine"
        embed.set_footer(text=f"{ctx.author.name} est classé #{user_rank} {suffix} avec {user_score} points.")

    await ctx.send(embed=embed)

@bot.command()
async def annonce_nouveautes(ctx):
    if ctx.channel.id != UPDATE_CHANNEL_ID:
        await ctx.send("Cette commande ne peut être utilisée que dans le fil dédié.")
        return

    quiz_role_mention = f"<@&{QUIZ_ROLE_ID}>"  # Idem pour ton rôle @QUIZ
    print(f"[DEBUG] Mention finale envoyée : {quiz_role_mention}")
    embed = discord.Embed(
        title="📢 Mise à jour du Bot Quiz Cinéma",
        description="De nouvelles fonctionnalités viennent d’arriver pour améliorer votre expérience ! 🎬🍿",
        color=0x1ABC9C  # turquoise sympa
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
        value=(
            "Un nouvel emoji 🚮 a été ajouté sur chaque question.\n"
            "Après 5 votes utilisateurs, la question est supprimée de la base."
        ),
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

    # 1️⃣ Ping dans un message classique
    await ctx.send(quiz_role_mention)
    # 2️⃣ Envoi de l’embed
    await ctx.send(embed=embed)

@bot.command()
async def aide(ctx):
    embed = discord.Embed(
        title="Aide du bot Quiz Cinéma",
        color=discord.Color.green()
    )
    embed.add_field(
        name="!q",
        value="Affiche une question cinéma aléatoire.",
        inline=False
    )
    embed.add_field(
        name="!sp",
        value="Affiche ton profil et tes statistiques.",
        inline=False
    )
    embed.add_field(
        name="!sr",
        value="Affiche le classement hebdomadaire.",
        inline=False
    )
    embed.add_field(
        name="!propose question | réponse",
        value="Propose une nouvelle question (ou utilise le format Q: ... R: ... ou Q : ... R : ...).",
        inline=False
    )
    embed.add_field(
        name="Quiz quotidien",
        value="Réagis avec l’emoji correspondant à ton score sous le message du quiz pour enregistrer tes points.",
        inline=False
    )
    await ctx.send(embed=embed)

@tasks.loop(hours=24)
async def daily_questions():
    await bot.wait_until_ready()
    channel = bot.get_channel(VALIDATED_CHANNEL_ID)

    # --- DIMANCHE à 10 questions ---
    today_weekday = datetime.datetime.now().weekday()  # 0=Lundi ... 6=Dimanche
    nb_questions = 10 if today_weekday == 6 else QUESTIONS_PAR_JOUR

    # 🔁 On récupère uniquement les questions non utilisées
    questions = await get_unused_questions()

    # Si on n'a pas assez de questions, on vide l'historique et on recharge
    if len(questions) < nb_questions:
        await reset_used_questions()
        questions = await get_unused_questions()

    if len(questions) < nb_questions:
        await channel.send(f"Pas assez de questions pour le quiz du jour ({nb_questions} nécessaires) !")
        return

    # Incrément du compteur de jours
    day = await get_day_count() + 1
    await set_day_count(day)

    # Message d’intro
    intro_msg = await get_jour_message(day)
    await channel.send(intro_msg)

    # Sélection aléatoire de questions et marquage comme utilisées
    selected = random.sample(questions, nb_questions)
    await mark_questions_used([q['id'] for q in selected])

    # Envoi des questions avec réactions
    for q in selected:
        msg = await channel.send(f"**Question :** {q['question']}\n||{q['answer']}||")
        await msg.add_reaction('✅')    # bonne réponse
        await msg.add_reaction('❌')    # mauvaise réponse
        await msg.add_reaction('🚮')    # signalement / suppression
        await asyncio.sleep(2)

    # Message pour enregistrer le score
    msg = await channel.send("@everyone Indiquez votre score du jour en réagissant ci-dessous :")
    for emoji in ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']:
        await msg.add_reaction(emoji)

@daily_questions.before_loop
async def before_daily_questions():
    now = datetime.datetime.now()
    target = now.replace(hour=HOUR_QUESTIONS_DAILY, minute=MINUTE_QUESTIONS_DAILY, second=0, microsecond=0)
    if target < now:
        target += datetime.timedelta(days=1)
    wait_seconds = (target - now).total_seconds()
    print(f"[DEBUG] Attente de {wait_seconds:.0f} secondes avant le prochain quiz quotidien ({target})")
    await asyncio.sleep(wait_seconds)

bot.run(DISCORD_TOKEN)
