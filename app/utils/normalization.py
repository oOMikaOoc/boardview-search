import re
import unicodedata
from pathlib import Path


def normalize_filename(filename):
    value = unicodedata.normalize("NFKD", filename or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[_\-.]+", " ", value)
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def safe_filename(filename):
    filename = Path(filename or "fichier_sans_nom").name
    filename = re.sub(r'[<>:"/\\|?*]+', "_", filename)
    filename = filename.strip().strip(".")
    return filename or "fichier_sans_nom"


def extension_for(filename):
    suffix = Path(filename or "").suffix.lower()
    return suffix[1:] if suffix else ""
