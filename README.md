# Boardview Search

Boardview Search is a local Flask web app for building a searchable library of boardview, schematic and technical repair files.

It can index files from Telegram channels and local folders, search across the indexed metadata, preview compatible files, and download remote files only when needed.

## Features

- Search boardview, schematic, PDF, archive, image and text files from one local web interface.
- Index public or accessible Telegram channels through a personal Telethon session.
- Add local folders or UNC/network shares as searchable sources.
- Preview compatible files directly in the browser: PDF, images and text.
- Download Telegram files on demand instead of downloading full channels up front.
- Store downloaded files outside Flask static folders.

## Requirements

- Python 3.11 or newer
- A Telegram account
- Telegram API credentials for Telegram indexing:
  - `TELEGRAM_API_ID`
  - `TELEGRAM_API_HASH`

## Installation

Clone the repository:

```powershell
git clone https://github.com/oOMikaOoc/boardview-search.git
cd boardview-search
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Configuration

Copy the example environment file:

```powershell
copy .env.example .env
```

Then edit `.env` and fill in your local settings:

```text
SECRET_KEY=change-me
ADMIN_PASSWORD=

TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_SESSION_NAME=telegram_session
```

The `.env` file is local to each installation. It is created from `.env.example`, then populated by the person running the app with their own Telegram credentials and local preferences.

By default:

- application data is stored in `data/`
- the SQLite database is stored in `data/app.db`
- downloaded files are stored in `Download/`
- the Telethon session is stored in `data/telegram_session/`

## Run

Start the app:

```powershell
python telegram_boardview_web.py
```

Open:

```text
http://127.0.0.1:5000/
```

## Telegram Login

Open the admin settings page:

```text
http://127.0.0.1:5000/admin/settings
```

Use `Connecter Telegram` to create the local Telethon session. Telegram may ask for:

- phone number
- login code
- two-factor authentication password, if enabled

The CLI login helper is also available:

```powershell
python telegram_login.py
```

## Sources

Sources are managed from:

```text
http://127.0.0.1:5000/admin/sources
```

### Telegram Source

Add a Telegram channel using its public name or identifier, for example:

```text
schematicslaptop
```

`max_messages_to_scan` controls how many messages are scanned when indexing. If left empty, `DEFAULT_TELEGRAM_SEARCH_LIMIT` from `.env` is used.

### Local Folder Source

Add a source of type:

```text
Dossier local / UNC
```

Examples:

```text
C:\Schemas
\\server\share\boardviews
```

Local indexing stores file metadata and local paths in the database. Files are then served through the controlled `/download/<file_id>` and `/view/<file_id>` routes.

The default `Download` folder is added automatically as a local source. If the database is moved to another computer, this default source is updated to point to the current computer's `Download` folder.

## How It Works

Search:

- queries the local database
- indexes active Telegram sources
- stores metadata only
- merges and deduplicates results
- does not download full files during search

Download:

- checks local storage first
- downloads from the remote source only if missing locally
- stores the file locally
- updates the database
- serves the file through `/download/<file_id>`

Preview:

- uses `/view/<file_id>`
- downloads on demand if needed
- supports PDF, images and text files
