import mimetypes
from pathlib import Path

from app.models import File
from app.services.log_service import app_log
from app.services.source_service import touch_indexed
from app.utils.normalization import extension_for, normalize_filename, safe_filename
from app.utils.storage import file_hash


def upsert_local_file(db, source, path):
    filename = safe_filename(path.name)
    normalized = normalize_filename(filename)
    stat = path.stat()
    remote_id = f"local:{source.id}:{str(path.resolve()).lower()}"
    digest = file_hash(path)

    existing = db.query(File).filter(File.remote_unique_id == remote_id).first()

    if not existing:
        existing = db.query(File).filter(File.hash == digest).first()

    if not existing:
        existing = (
            db.query(File)
            .filter(File.normalized_filename == normalized, File.size == stat.st_size)
            .first()
        )

    created = existing is None
    file_record = existing or File(source_id=source.id, source_type=source.type)

    file_record.source_id = source.id
    file_record.source_type = source.type
    file_record.remote_unique_id = remote_id
    file_record.title = filename
    file_record.filename = filename
    file_record.normalized_filename = normalized
    file_record.extension = extension_for(filename)
    file_record.mime_type = mimetypes.guess_type(filename)[0]
    file_record.size = stat.st_size
    file_record.message_date = None
    file_record.caption = str(path)
    file_record.downloaded = True
    file_record.local_path = str(path.resolve())
    file_record.hash = digest

    if created:
        db.add(file_record)

    db.commit()
    return file_record, created


def index_source(db, source, progress_callback=None):
    root = Path(source.identifier).expanduser()

    if not root.exists():
        raise ValueError(f"Chemin local introuvable : {source.identifier}")

    if root.is_file():
        files = [root]
    else:
        files = [path for path in root.rglob("*") if path.is_file()]

    indexed = 0
    created = 0
    total = len(files)

    if progress_callback:
        progress_callback({"source": source.name, "type": "local_folder", "scanned": 0, "limit": total, "indexed": 0})

    for path in files:
        _, was_created = upsert_local_file(db, source, path)
        indexed += 1
        created += 1 if was_created else 0
        if progress_callback and (indexed == 1 or indexed % 50 == 0 or indexed == total):
            progress_callback({"source": source.name, "type": "local_folder", "scanned": indexed, "limit": total, "indexed": indexed})

    touch_indexed(db, source)
    app_log(f"Source locale indexee : {source.name} ({indexed} fichiers, {created} nouveaux)")
    return {"indexed": indexed, "created": created, "limit": len(files)}
