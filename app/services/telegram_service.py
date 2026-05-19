import asyncio
from pathlib import Path
from threading import Lock

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from app.config import Config
from app.models import File, Source, utcnow
from app.services.log_service import app_log
from app.services.settings_service import telegram_config
from app.services.source_service import source_limit, touch_indexed
from app.utils.normalization import extension_for, normalize_filename, safe_filename
from app.utils.storage import file_hash, local_path_for

telegram_lock = Lock()


def run_telegram(coro):
    with telegram_lock:
        return asyncio.run(coro)


def _session_file(db):
    config = telegram_config(db)
    session_name = config["session_name"] or "telegram_session"
    session_path = Config.TELEGRAM_SESSION_PATH / session_name
    session_path.parent.mkdir(parents=True, exist_ok=True)
    return str(session_path)


def _client(db):
    config = telegram_config(db)

    if not config["api_id"] or not config["api_hash"]:
        raise ValueError("Configuration Telegram incomplete : API ID/API HASH manquants.")

    return TelegramClient(_session_file(db), int(config["api_id"]), config["api_hash"])


async def test_connection(db):
    async with _client(db) as client:
        if not await client.is_user_authorized():
            return {"ok": False, "error": "Session Telegram non connectee. Lance une connexion Telethon interactive une premiere fois."}

        me = await client.get_me()
        display = " ".join(part for part in [getattr(me, "first_name", ""), getattr(me, "last_name", "")] if part)
        return {"ok": True, "user": display or getattr(me, "username", "") or str(me.id)}


async def message_count(db, identifier):
    async with _client(db) as client:
        if not await client.is_user_authorized():
            raise ValueError("Session Telegram non connectee.")

        messages = await client.get_messages(identifier, limit=0)
        return getattr(messages, "total", 0)


async def send_login_code(db, phone):
    client = _client(db)
    await client.connect()
    try:
        sent = await client.send_code_request(phone)
        return {"ok": True, "phone_code_hash": sent.phone_code_hash}
    finally:
        await client.disconnect()


async def complete_login(db, phone, code, phone_code_hash, password=None):
    client = _client(db)
    await client.connect()
    try:
        try:
            await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        except SessionPasswordNeededError:
            if not password:
                return {"ok": False, "needs_password": True, "error": "Mot de passe 2FA requis."}
            await client.sign_in(password=password)

        me = await client.get_me()
        display = " ".join(part for part in [getattr(me, "first_name", ""), getattr(me, "last_name", "")] if part)
        return {"ok": True, "user": display or getattr(me, "username", "") or str(me.id)}
    finally:
        await client.disconnect()


def message_filename(message):
    if not message.file:
        return ""

    return message.file.name or f"telegram_{message.id}"


def document_id(message):
    document = getattr(message, "document", None)
    return str(getattr(document, "id", "")) if document else None


def remote_unique_id(source, message):
    doc_id = document_id(message)
    if doc_id:
        return f"telegram:{source.identifier}:{doc_id}"
    return f"telegram:{source.identifier}:{message.id}"


def upsert_file_from_message(db, source, message):
    if not message.file:
        return None, False

    filename = safe_filename(message_filename(message))
    normalized = normalize_filename(filename)
    size = getattr(message.file, "size", None)
    doc_id = document_id(message)
    remote_id = remote_unique_id(source, message)

    existing = (
        db.query(File)
        .filter(File.source_id == source.id, File.telegram_message_id == message.id)
        .first()
    )

    if not existing and remote_id:
        existing = db.query(File).filter(File.remote_unique_id == remote_id).first()

    if not existing and doc_id:
        existing = db.query(File).filter(File.telegram_document_id == doc_id).first()

    if not existing:
        existing = (
            db.query(File)
            .filter(File.normalized_filename == normalized, File.size == size)
            .first()
        )

    created = existing is None
    file_record = existing or File(source_id=source.id, source_type=source.type)

    file_record.source_id = source.id
    file_record.source_type = source.type
    file_record.telegram_channel_id = str(source.identifier)
    file_record.telegram_message_id = message.id
    file_record.telegram_document_id = doc_id
    file_record.remote_unique_id = remote_id
    file_record.title = filename
    file_record.filename = filename
    file_record.normalized_filename = normalized
    file_record.extension = extension_for(filename)
    file_record.mime_type = getattr(message.file, "mime_type", None)
    file_record.size = size
    file_record.message_date = message.date.replace(tzinfo=None) if message.date else None
    file_record.caption = (message.raw_text or "").strip() or None

    if created:
        db.add(file_record)

    db.commit()
    return file_record, created


async def index_source(db, source, progress_callback=None):
    if source.type != "telegram":
        raise ValueError(f"Type de source non supporte : {source.type}")

    indexed = 0
    created = 0
    limit = source_limit(source)

    scanned = 0

    if progress_callback:
        progress_callback({"source": source.name, "type": "telegram", "scanned": 0, "limit": limit, "indexed": indexed})

    async with _client(db) as client:
        async for message in client.iter_messages(source.identifier, limit=limit):
            scanned += 1
            if progress_callback and (scanned == 1 or scanned % 50 == 0):
                progress_callback({"source": source.name, "type": "telegram", "scanned": scanned, "limit": limit, "indexed": indexed})

            if not message.file:
                continue

            _, was_created = upsert_file_from_message(db, source, message)
            indexed += 1
            created += 1 if was_created else 0

    if progress_callback:
        progress_callback({"source": source.name, "type": "telegram", "scanned": scanned, "limit": limit, "indexed": indexed})

    touch_indexed(db, source)
    app_log(f"Source indexee : {source.name} ({indexed} fichiers, {created} nouveaux)")
    return {"indexed": indexed, "created": created, "limit": limit}


async def index_active_telegram_sources(db):
    results = []
    sources = db.query(Source).filter_by(type="telegram", enabled=True).all()

    for source in sources:
        results.append((source, await index_source(db, source)))

    return results


async def download_file(db, file_record):
    if file_record.source_type != "telegram":
        raise ValueError("Source distante non supportee pour le telechargement.")

    source = db.query(Source).filter_by(id=file_record.source_id).first()
    if not source:
        raise ValueError("Source introuvable.")

    if file_record.size and file_record.size > Config.MAX_DOWNLOAD_SIZE_MB * 1024 * 1024:
        raise ValueError("Fichier trop gros pour la limite configuree.")

    relative_path, absolute_path = local_path_for(file_record)

    async with _client(db) as client:
        message = await client.get_messages(source.identifier, ids=int(file_record.telegram_message_id))

        if not message or not message.file:
            raise ValueError("Message Telegram introuvable ou fichier supprime.")

        downloaded_path = await message.download_media(file=str(absolute_path))

    if not downloaded_path:
        raise ValueError("Telechargement Telegram vide.")

    downloaded_path = Path(downloaded_path)
    file_record.local_path = str(relative_path)
    file_record.downloaded = True
    file_record.downloaded_at = utcnow()
    file_record.hash = file_hash(downloaded_path)
    file_record.size = downloaded_path.stat().st_size
    db.commit()

    app_log(f"Fichier telecharge : {file_record.filename}")
    return downloaded_path
