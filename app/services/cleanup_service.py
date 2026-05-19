from pathlib import Path

from app.models import File
from app.services.log_service import app_log
from app.utils.storage import absolute_storage_path


def file_exists(file_record):
    if not file_record.local_path:
        return False

    if file_record.source_type == "local_folder":
        return Path(file_record.local_path).exists()

    return absolute_storage_path(Path(file_record.local_path)).exists()


def clean_missing_local_files(db, delete_local_sources=True):
    checked = 0
    cleaned = 0

    query = db.query(File).filter(File.local_path.isnot(None))
    if not delete_local_sources:
        query = query.filter(File.source_type != "local_folder")

    for file_record in query.all():
        checked += 1

        if file_exists(file_record):
            continue

        if file_record.source_type == "local_folder":
            db.delete(file_record)
        else:
            file_record.downloaded = False
            file_record.local_path = None
            file_record.hash = None
            file_record.downloaded_at = None

        cleaned += 1

    db.commit()
    app_log(f"Nettoyage fichiers absents : {cleaned}/{checked}")
    return {"checked": checked, "cleaned": cleaned}
