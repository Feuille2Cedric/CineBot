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
            ORDER BY RANDOM() LIMIT 20;  -- On prend plus de films pour garantir une meilleure diversité
            """
            # Utiliser self.bot.pool pour interagir avec la base de données
            movies = await self.bot.pool.fetch(query)

            # Si aucun film n'est récupéré
            if not movies:
                await ctx.send("Aucun film n'a été récupéré, vérifier la base de données.")
                print("Aucun film récupéré depuis la base de données.")
                return

            print(f"Films récupérés : {movies}")  # Log des films récupérés

            # Sélectionner 4 films aléatoires parmi ceux récupérés
            selected_movies = random.sample(movies, 4)

            # Générer une question aléatoire
            question_type = random.choice([
                "oldest",  # Le plus vieux
                "newest",  # Le plus récent
                "genre",   # Genre spécifique
            ])

            # Initialiser la bonne réponse
            correct_answer = None
            question = ""

            # Sélectionner la bonne question et la bonne réponse
            if question_type == "oldest":
                # Trouver le film le plus vieux parmi les 4 films
                oldest_movie = min(selected_movies, key=lambda x: x['release_date'])
                correct_answer = oldest_movie['franchise']
                question = f"Parmi ces films, lequel est le plus vieux ?"

            elif question_type == "newest":
                # Trouver le film le plus récent parmi les 4 films
                newest_movie = max(selected_movies, key=lambda x: x['release_date'])
                correct_answer = newest_movie['franchise']
                question = f"Parmi ces films, lequel est le plus récent ?"

            elif question_type == "genre":
                # Choisir un genre spécifique (ex: Comédie)
                genre = random.choice(["Comédie", "Drame", "Action", "Animation", "Science-Fiction"])

                # Filtrer les films par genre
                genre_movies = [movie for movie in selected_movies if genre in movie['genre']]

                # Si on a moins de 1 film du genre parmi les 4 films, on doit prendre un film de ce genre
                if len(genre_movies) == 0:
                    # Compléter avec des films d'autres genres
                    genre_movies = [random.choice([movie for movie in movies if genre in movie['genre']])]
                    selected_movies = random.sample([movie for movie in movies if genre in movie['genre']], 4)

                # Mélanger les films pour ajouter de la diversité
                random.shuffle(selected_movies)
                genre_movies = genre_movies[:1]

                # La bonne réponse est le film du genre choisi
                correct_answer = genre_movies[0]['franchise']
                question = f"Parmi ces films, lequel appartient au genre {genre} ?"

            print(f"Question posée : {question}")  # Log de la question générée

            # Envoyer la question
            msg = await ctx.send(question)

            # Ajouter les réactions avec les films
            options = []
            for idx, movie in enumerate(selected_movies, start=1):
                options.append(f"{idx}. {movie['franchise']}")  # Nom du film pour chaque option
            options_text = "\n".join(options)

            # Envoyer les options (réponses possibles) après la question
            await msg.edit(content=f"{question}\n\n{options_text}")

            # Envoyer la bonne réponse en spoiler après les options
            await ctx.send(f"**La bonne réponse est :** ||{correct_answer}||")

            # Réactions pour chaque film
            for idx in range(4):
                await msg.add_reaction(f"{idx+1}\u20e3")  # Emoji 1️⃣, 2️⃣, 3️⃣, 4️⃣

            # Attendre la réponse (mais sans bloquer les autres commandes)
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ['1️⃣', '2️⃣', '3️⃣', '4️⃣']

            # Attendre la réaction sans bloquer la suite
            reaction = await self.bot.wait_for('reaction_add', check=check)

            # Vérifier la réponse
            answer_index = ['1️⃣', '2️⃣', '3️⃣', '4️⃣'].index(str(reaction.emoji)) + 1

        except Exception as e:
            print(f"Erreur dans la commande !devinette: {e}")
            await ctx.send("Une erreur est survenue. Veuillez réessayer plus tard.")
        

async def setup(bot):
    if bot.get_cog("DevinetteCmd") is None:
        await bot.add_cog(DevinetteCmd(bot))
