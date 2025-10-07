import random
from discord.ext import commands
from app.domain.repositories import QuestionRepo

class DevinetteCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.qrepo: QuestionRepo = bot.repos["questions"]

    @commands.command(name="devinette")
    async def devinette(self, ctx):
        # Choisir 4 films au hasard avec leurs métadonnées
        query = """
        SELECT q.id, q.question, q.answer, qm.category, qm.genre, qm.release_date, qm.rating, qm.franchise
        FROM questions q
        JOIN question_metadata qm ON q.id = qm.question_id
        ORDER BY RANDOM() LIMIT 4;
        """
        movies = await self.bot.db.fetch(query)

        print(f"Films récupérés : {movies}")  # Affiche les films récupérés

        # Vérifier si des films sont récupérés
        if not movies:
            await ctx.send("Aucun film n'a été récupéré, vérifier la base de données.")
            return

        # Générer une question aléatoire
        question_type = random.choice([
            "oldest",  # Le plus vieux
            "newest",  # Le plus récent
            "genre",   # Genre spécifique
        ])

        if question_type == "oldest":
            # Trouver le film le plus vieux
            oldest_movie = min(movies, key=lambda x: x['release_date'])
            correct_answer = oldest_movie['id']
            question = f"Parmi ces films, lequel est le plus vieux ?"

        elif question_type == "newest":
            # Trouver le film le plus récent
            newest_movie = max(movies, key=lambda x: x['release_date'])
            correct_answer = newest_movie['id']
            question = f"Parmi ces films, lequel est le plus récent ?"

        elif question_type == "genre":
            # Choisir un genre spécifique (ex: Comédie)
            genre = random.choice(["Comédie", "Drame", "Action", "Animation", "Science-Fiction"])
            genre_movies = [movie for movie in movies if genre in movie['genre']]
            correct_answer = random.choice(genre_movies)['id']
            question = f"Parmi ces films, lequel appartient au genre {genre} ?"

        print(f"Question posée : {question}")  # Affiche la question générée

        # Envoyer la question
        msg = await ctx.send(question)

        # Réactions pour chaque film
        for idx, movie in enumerate(movies, start=1):
            await msg.add_reaction(f"{idx}\u20e3")  # Emoji 1️⃣, 2️⃣, 3️⃣...

        # Attendre la réponse
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['1️⃣', '2️⃣', '3️⃣', '4️⃣']

        reaction = await self.bot.wait_for('reaction_add', check=check)

        # Vérifier la réponse
        answer_index = ['1️⃣', '2️⃣', '3️⃣', '4️⃣'].index(str(reaction.emoji)) + 1
        if movies[answer_index - 1]['id'] == correct_answer:
            await ctx.send("Bravo, tu as trouvé la bonne réponse ! 🎉")
        else:
            await ctx.send(f"Dommage, la bonne réponse était : le film **{movies[correct_answer - 1]['question']}**.")

async def setup(bot):
    if bot.get_cog("DevinetteCmd") is None:
        await bot.add_cog(DevinetteCmd(bot))
