# Boardview Search

Application Flask locale pour indexer, rechercher, afficher et telecharger a la demande des fichiers provenant de sources techniques.

Pour le moment, le connecteur implemente est Telegram via une session utilisateur Telethon.

## Configuration

1. Copie `.env.example` vers `.env`.
2. Renseigne au minimum :

```text
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_SESSION_NAME=telegram_session
```

`TELEGRAM_SESSION_NAME` est simplement le nom du fichier de session Telethon. La valeur par defaut convient dans la plupart des cas.

Les fichiers sont stockes hors `/static`, par defaut dans un dossier unique :

```text
Download
```

La session Telethon est stockee dans :

```text
data/telegram_session
```

En Docker, monte le dossier `/data` ou configure `DATA_PATH=/data`.

## Publication GitHub

Le depot peut contenir le code, les templates, `requirements.txt`, les scripts `.bat`, `README.md`, `.env.example` et `.gitignore`.

Ne publie pas ces elements :

- `.env` : identifiants Telegram et cle Flask locale.
- `data/` : base SQLite, logs, index, chemins locaux et session Telethon.
- `Download/` : fichiers telecharges.
- `__pycache__/`, `.venv/`, `.qodo/` : artefacts locaux.

## Lancer l'application

```powershell
python telegram_boardview_web.py
```

Puis ouvrir :

```text
http://127.0.0.1:5000/
```

## Installation sur le PC d'atelier

Copie le dossier complet `TelegramDownload` sur le PC d'atelier, puis lance une premiere fois :

```powershell
install_atelier.bat
```

Ce script cree un environnement virtuel local `.venv`, installe les dependances de `requirements.txt`, et cree `.env` depuis `.env.example` s'il manque.

Ensuite, pour demarrer l'application en double-clic :

```powershell
start_atelier.bat
```

Le navigateur s'ouvre sur :

```text
http://127.0.0.1:5000/
```

Pour conserver l'index, les fichiers deja telecharges et la session Telegram, copie aussi les dossiers :

```text
data
Download
```

## Connexion Telegram

La premiere connexion Telethon peut demander le telephone, le code Telegram et le mot de passe 2FA.

L'admin permet de connecter et tester la session :

```text
http://127.0.0.1:5000/admin/settings
```

Le bouton `Connecter Telegram` lance le flux telephone -> code -> 2FA optionnelle.

Le script CLI reste disponible comme solution de secours :

```powershell
python telegram_login.py
```

Telethon demandera le numero, le code Telegram et la 2FA si necessaire.

Test direct :

```text
http://127.0.0.1:5000/admin/telegram/test
```

## Ajouter une source Telegram

Ouvre :

```text
http://127.0.0.1:5000/admin/sources
```

Ajoute un canal Telegram avec son nom public, par exemple :

```text
schematicslaptop
```

Definis `max_messages_to_scan` selon la taille du canal. Si vide, la valeur `DEFAULT_TELEGRAM_SEARCH_LIMIT` est utilisee.

## Ajouter une source locale

Dans `/admin/sources`, ajoute une source de type :

```text
Dossier local / UNC
```

Exemples :

```text
C:\Schemas
\\serveur\partage\boardviews
```

L'indexation locale parcourt les fichiers, enregistre les metadonnees et le chemin local, puis les sert via les routes controlees `/download/<file_id>` et `/view/<file_id>`.

Le dossier `Download` est ajoute comme source locale par defaut. Si tu copies la base sur un autre PC, cette source par defaut est automatiquement recalee vers le dossier `Download` du PC courant. Les telechargements faits depuis Telegram arrivent aussi directement dans ce dossier, sans sous-dossier par marque.

## Logique principale

Recherche :
- interroge la base locale,
- indexe les sources Telegram actives,
- enregistre uniquement les metadonnees,
- fusionne et dedoublonne les resultats,
- ne telecharge jamais les fichiers complets.

Telechargement :
- verifie d'abord le stockage local,
- si absent, telecharge depuis la source distante,
- stocke le fichier localement,
- met a jour la base,
- sert le fichier via `/download/<file_id>`.

Affichage :
- passe par `/view/<file_id>`,
- telecharge a la demande si necessaire,
- affiche uniquement les types compatibles : PDF, images et textes.
