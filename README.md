# 🎬 CineBot – Quiz Cinéma Discord

CineBot est un bot Discord asynchrone qui propose chaque jour un quiz cinéma, gère les scores, le classement, et permet à la communauté de proposer de nouvelles questions.  
Il utilise une base de données PostgreSQL pour stocker toutes les données.

---

## 🚀 Fonctionnalités

- Quiz cinéma quotidien avec 5 questions aléatoires
- Gestion automatique du jour du quiz
- Classements quotidien, hebdomadaire, mensuel et total
- Commande de profil personnel
- Propositions de questions par la communauté, avec validation par réaction
- 100% base de données PostgreSQL (plus de fichiers JSON)
- Compatible Railway/Nixpacks

---

## 🛠️ Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/ton-utilisateur/cinebot.git
cd cinebot
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Variables d’environnement à définir

Crée un fichier `.env` (ou configure les variables sur Railway) :

```bash
DATABASE_URL=postgresql://user:password@host:port/dbname
DISCORD_TOKEN=TON_TOKEN_DISCORD
PROPOSAL_CHANNEL_ID=123456789012345678
VALIDATED_CHANNEL_ID=123456789012345678
COMMANDS_CHANNEL_ID=123456789012345678
HOUR_QUESTIONS_DAILY=19
MINUTE_QUESTIONS_DAILY=42
CHECKS_REQUIRED=1
```

> Les IDs de salons sont à récupérer via Discord (clic droit sur le salon → Copier l’identifiant).

### 4. Lancer le bot

```bash
python main.py
```

---

## 📋 Commandes principales

| Commande      | Description                                                |
|---------------|-----------------------------------------------------------|
| `!q`          | Affiche une question aléatoire (salon de commandes)       |
| `!sp`         | Affiche ton profil et tes scores                          |
| `!sr`         | Affiche le classement hebdomadaire                        |
| `!propose`    | Propose une question au format `question | réponse`       |

---

## 💡 Proposer une question

Dans le salon de propositions, tu peux :
- Utiliser la commande :  

```bash
!propose Quelle année est sorti "Le Parrain" ? | 1972
```

- Ou écrire directement :

```bash
Q: Quel acteur joue Neo dans Matrix ?
R: ||Keanu Reeves||
```

- Une réaction ✅ permet de valider l’ajout dans la base (nombre de validations configurable).

---

## 🗃️ Structure de la base de données

- **questions** : stocke toutes les questions/réponses
- **scores_daily** : scores par utilisateur et par jour
- **day_count** : numéro du jour courant du quiz
- **messages_jour** : messages personnalisés pour certains jours

---

## 🏗️ Déploiement sur Railway

1. Crée un nouveau projet Railway.
2. Ajoute une base PostgreSQL Railway et récupère l’URL.
3. Ajoute toutes les variables d’environnement dans l’onglet “Variables”.
4. Pousse ton code sur Railway (GitHub ou Railway CLI).
5. Le bot démarre automatiquement à chaque build.

---

## 🧑‍💻 Contribuer

Les contributions sont les bienvenues !  
N’hésite pas à ouvrir une issue ou une pull request pour toute suggestion ou correction.

---

## 📄 Licence

MIT

---

## 🙏 Remerciements

- [discord.py](https://github.com/Rapptz/discord.py)
- [asyncpg](https://github.com/MagicStack/asyncpg)
- Railway pour l’hébergement facile

**Bon quiz ! 🎬🍿**
