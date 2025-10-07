import random
from discord.ext import commands

class DevinetteCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="devinette")
    async def devinette(self, ctx):
        try:
            # Choisir 4 films au hasard avec leurs métadonnées
            query = """
            SELECT category, genre, release_date, rating, franchise
            FROM question_metadata
            ORDER BY RANDOM() LIMIT 4;
            """
            movies = await self.bot.pool.fetch(query)

            # Si aucun film n'est récupéré
            if not movies:
                await ctx.send("Aucun film n'a été récupéré, vérifier la base de données.")
                print("Aucun film récupéré depuis la base de données.")
                return

            print(f"Films récupérés : {movies}")  # Log de films récupérés

            # Générer une question aléatoire
            question_type = random.choice([
                "oldest",  # Le plus vieux
                "newest",  # Le plus récent
                "genre",   # Genre spécifique
            ])

            if question_type == "oldest":
                # Trouver le film le plus vieux
                oldest_movie = min(movies, key=lambda x: x['release_date'])
                correct_answer = oldest_movie['franchise']  # Nous pouvons comparer la franchise pour la réponse
                question = f"Parmi ces films, lequel est le plus vieux ?"

            elif question_type == "newest":
                # Trouver le film le plus récent
                newest_movie = max(movies, key=lambda x: x['release_date'])
                correct_answer = newest_movie['franchise']  # Nous pouvons comparer la franchise pour la réponse
                question = f"Parmi ces films, lequel est le plus récent ?"

            elif question_type == "genre":
                # Choisir un genre spécifique (ex: Comédie)
                genre = random.choice(["Comédie", "Drame", "Action", "Animation", "Science-Fiction"])
                genre_movies = [movie for movie in movies if genre in movie['genre']]
                correct_answer = random.choice(genre_movies)['franchise']  # Compare la franchise pour la réponse
                question = f"Parmi ces films, lequel appartient au genre {genre} ?"

            print(f"Question posée : {question}")  # Log de la question générée

            # Envoyer la question
            msg = await ctx.send(question)

            # Réactions pour chaque film (vérifier qu'on ajoute bien 4 réactions)
            for idx, movie in enumerate(movies, start=1):
                await msg.add_reaction(f"{idx}\u20e3")  # Emoji 1️⃣, 2️⃣, 3️⃣...

            # Attendre la réponse
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ['1️⃣', '2️⃣', '3️⃣', '4️⃣']

            reaction = await self.bot.wait_for('reaction_add', check=check)

            # Vérifier la réponse
            answer_index = ['1️⃣', '2️⃣', '3️⃣', '4️⃣'].index(str(reaction.emoji)) + 1
            if movies[answer_index - 1]['franchise'] == correct_answer:
                await ctx.send("Bravo, tu as trouvé la bonne réponse ! 🎉")
            else:
                await ctx.send(f"Dommage, la bonne réponse était : le film **{movies[correct_answer - 1]['franchise']}**.")

        except Exception as e:
            print(f"Erreur dans la commande !devinette: {e}")
            await ctx.send("Une erreur est survenue. Veuillez réessayer plus tard.")
        

async def setup(bot):
    if bot.get_cog("DevinetteCmd") is None:
        await bot.add_cog(DevinetteCmd(bot))
