import hashlib
import mimetypes
from pathlib import Path

from app.config import Config
from app.utils.normalization import safe_filename


VIEWABLE_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "webp", "gif", "txt", "log", "csv", "json", "xml", "md"}


def relative_file_path(file_record):
    filename = safe_filename(file_record.filename)
    folder_name = safe_filename(Path(filename).stem) or str(file_record.id)
    relative = Path(folder_name) / filename
    candidate = Config.STORAGE_PATH / relative

    if not candidate.exists() or file_record.local_path == str(relative):
        return relative

    stem = candidate.stem
    suffix = candidate.suffix
    return Path(folder_name) / f"{stem}_{file_record.id}{suffix}"


def absolute_storage_path(relative_path):
    return Config.STORAGE_PATH / relative_path


def local_path_for(file_record):
    relative = relative_file_path(file_record)
    absolute = absolute_storage_path(relative)
    Config.STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    return relative, absolute


def existing_local_path(file_record):
    if not file_record.local_path:
        return None

    if file_record.source_type == "local_folder":
        path = Path(file_record.local_path)
        return path if path.exists() and path.is_file() else None

    path = absolute_storage_path(Path(file_record.local_path))
    return path if path.exists() and path.is_file() else None


def file_hash(path):
    digest = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def is_viewable(file_record):
    extension = (file_record.extension or "").lower()
    return extension in VIEWABLE_EXTENSIONS


def mimetype_for(file_record):
    return file_record.mime_type or mimetypes.guess_type(file_record.filename or "")[0] or "application/octet-stream"
