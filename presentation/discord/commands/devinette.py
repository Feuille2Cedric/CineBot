import random
from discord.ext import commands

class DevinetteCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="devinette")
    async def devinette(self, ctx):
        try:
            # Choisir 20 films au hasard avec leurs métadonnées
            query = """
            SELECT category, genre, release_date, franchise
            FROM question_metadata
            ORDER BY RANDOM() LIMIT 20;
            """
            # Utiliser self.bot.pool pour interagir avec la base de données
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

            # Initialiser genre_movies
            genre_movies = []

            # Sélectionner la bonne question et la bonne réponse
            if question_type == "oldest":
                # Trouver le film le plus vieux
                oldest_movie = min(movies, key=lambda x: x['release_date'])
                correct_answer = oldest_movie['franchise']  # Nous pouvons comparer la franchise pour la réponse
                question = f"Parmi ces films, lequel est le plus vieux ?"
                genre_movies = [oldest_movie]  # Le film le plus vieux est le premier

            elif question_type == "newest":
                # Trouver le film le plus récent
                newest_movie = max(movies, key=lambda x: x['release_date'])
                correct_answer = newest_movie['franchise']  # Nous pouvons comparer la franchise pour la réponse
                question = f"Parmi ces films, lequel est le plus récent ?"
                genre_movies = [newest_movie]  # Le film le plus récent est le premier

            elif question_type == "genre":
                # Choisir un genre spécifique (ex: Comédie)
                genre = random.choice(["Comédie", "Drame", "Action", "Animation", "Science-Fiction"])

                # Filtrer les films par genre
                genre_movies = [movie for movie in movies if genre in movie['genre']]

                # Si on a moins de 4 films du genre, ajouter des films d'autres genres
                if len(genre_movies) < 4:
                    remaining_movies = [movie for movie in movies if genre not in movie['genre']]
                    while len(genre_movies) < 4 and remaining_movies:
                        genre_movies.append(remaining_movies.pop())

                # Mélanger les films pour ajouter de la diversité
                random.shuffle(genre_movies)

                # La bonne réponse est le premier film du genre
                correct_answer = genre_movies[0]['franchise']
                question = f"Parmi ces films, lequel appartient au genre {genre} ?"

            print(f"Question posée : {question}")  # Log de la question générée

            # Envoyer la question
            msg = await ctx.send(question)

            # Ajouter les réactions avec les films
            options = []
            for idx, movie in enumerate(genre_movies, start=1):
                options.append(f"{idx}. {movie['franchise']}")  # Nom du film pour chaque option
            options_text = "\n".join(options)

            # Envoyer les options (réponses possibles) après la question
            await msg.edit(content=f"{question}\n\n{options_text}")

            # Envoyer la bonne réponse en spoiler après les options
            await ctx.send(f"**La bonne réponse est :** ||{correct_answer}||")

            # Réactions pour chaque film
            for idx in range(4):
                await msg.add_reaction(f"{idx+1}\u20e3")  # Emoji 1️⃣, 2️⃣, 3️⃣, 4️⃣

            # Attendre la réponse
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ['1️⃣', '2️⃣', '3️⃣', '4️⃣']

            reaction = await self.bot.wait_for('reaction_add', check=check)

            # Vérifier la réponse
            answer_index = ['1️⃣', '2️⃣', '3️⃣', '4️⃣'].index(str(reaction.emoji)) + 1
            if genre_movies[answer_index - 1]['franchise'] == correct_answer:
                await ctx.send("Bravo, tu as trouvé la bonne réponse ! 🎉")
            else:
                await ctx.send(f"Dommage, la bonne réponse était : ||{correct_answer}||.")

        except Exception as e:
            print(f"Erreur dans la commande !devinette: {e}")
            await ctx.send("Une erreur est survenue. Veuillez réessayer plus tard.")
        

async def setup(bot):
    if bot.get_cog("DevinetteCmd") is None:
        await bot.add_cog(DevinetteCmd(bot))
