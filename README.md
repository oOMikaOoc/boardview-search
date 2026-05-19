# Boardview Search

Boardview Search est une application web locale en Flask pour créer une bibliothèque consultable de fichiers boardview, schémas et documents techniques de réparation.

L'application peut indexer des fichiers depuis des canaux Telegram et des dossiers locaux, rechercher dans les métadonnées, prévisualiser les fichiers compatibles, et télécharger les fichiers distants uniquement à la demande.

Note de transparence : à l'ère de l'IA, une partie de ce projet a été vibe codé avec l'aide d'assistants IA, puis adaptée, testée et utilisée sur des besoins réels de réparation.

## Fonctionnalités

- Recherche de fichiers boardview, schémas, PDF, archives, images et textes depuis une interface web locale.
- Indexation de canaux Telegram publics ou accessibles via une session Telethon personnelle.
- Ajout de dossiers locaux ou de partages réseau/UNC comme sources de recherche.
- Prévisualisation dans le navigateur pour les PDF, images et fichiers texte.
- Téléchargement des fichiers Telegram uniquement à la demande, sans aspirer tout un canal.
- Stockage des fichiers téléchargés en dehors des dossiers statiques Flask.

## Prérequis

- Python 3.11 ou plus récent
- Un compte Telegram
- Des identifiants API Telegram pour l'indexation :
  - `TELEGRAM_API_ID`
  - `TELEGRAM_API_HASH`

## Installation

Cloner le dépôt :

```powershell
git clone https://github.com/oOMikaOoc/boardview-search.git
cd boardview-search
```

Créer et activer un environnement virtuel :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Installer les dépendances :

```powershell
pip install -r requirements.txt
```

## Configuration

Copier le fichier d'exemple :

```powershell
copy .env.example .env
```

Modifier ensuite `.env` avec les paramètres locaux :

```text
SECRET_KEY=change-me
ADMIN_PASSWORD=

TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_SESSION_NAME=telegram_session
```

Le fichier `.env` est propre à chaque installation. Il est créé depuis `.env.example`, puis rempli par la personne qui utilise l'application avec ses propres identifiants Telegram et ses préférences locales.

Par défaut :

- les données de l'application sont stockées dans `data/`
- la base SQLite est stockée dans `data/app.db`
- les fichiers téléchargés sont stockés dans `Download/`
- la session Telethon est stockée dans `data/telegram_session/`

## Lancement

Démarrer l'application :

```powershell
python telegram_boardview_web.py
```

Ouvrir ensuite :

```text
http://127.0.0.1:5000/
```

## Connexion Telegram

Ouvrir la page des paramètres admin :

```text
http://127.0.0.1:5000/admin/settings
```

Utiliser `Connecter Telegram` pour créer la session Telethon locale. Telegram peut demander :

- le numéro de téléphone
- le code de connexion
- le mot de passe de double authentification, si activé

Le script de connexion en ligne de commande reste disponible :

```powershell
python telegram_login.py
```

## Sources

Les sources se gèrent depuis :

```text
http://127.0.0.1:5000/admin/sources
```

### Source Telegram

Ajouter un canal Telegram avec son nom public ou son identifiant, par exemple :

```text
schematicslaptop
```

`max_messages_to_scan` définit le nombre de messages à parcourir pendant l'indexation. Si le champ est vide, la valeur `DEFAULT_TELEGRAM_SEARCH_LIMIT` du fichier `.env` est utilisée.

### Source dossier local

Ajouter une source de type :

```text
Dossier local / UNC
```

Exemples :

```text
C:\Schemas
\\serveur\partage\boardviews
```

L'indexation locale enregistre les métadonnées des fichiers et leurs chemins dans la base. Les fichiers sont ensuite servis via les routes contrôlées `/download/<file_id>` et `/view/<file_id>`.

Le dossier `Download` est ajouté automatiquement comme source locale par défaut. Si la base est déplacée sur un autre ordinateur, cette source par défaut est mise à jour vers le dossier `Download` de l'ordinateur courant.

## Fonctionnement

Recherche :

- interroge la base locale
- indexe les sources Telegram actives
- enregistre uniquement les métadonnées
- fusionne et dédoublonne les résultats
- ne télécharge pas les fichiers complets pendant la recherche

Téléchargement :

- vérifie d'abord le stockage local
- télécharge depuis la source distante uniquement si le fichier est absent localement
- stocke le fichier localement
- met à jour la base
- sert le fichier via `/download/<file_id>`

Prévisualisation :

- passe par `/view/<file_id>`
- télécharge à la demande si nécessaire
- prend en charge les PDF, images et fichiers texte

## Communauté

Vous connaissez un canal Telegram utile pour la réparation, les boardviews ou les schémas ? Les suggestions de sources et les retours d'utilisation sont les bienvenus via Discord :

```text
https://discord.gg/RbZMajrDRD
```

Retrouvez aussi mes liens et moyens de soutien ici :

```text
https://linkvault.hackncraft.fr/p/oomikaooc
https://buymeacoffee.com/oomikaooc
```
