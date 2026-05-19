from app.services.local_source_service import index_source as index_local_source
from app.services.telegram_service import index_source as index_telegram_source
from app.services.telegram_service import run_telegram


def index_source(db, source, progress_callback=None):
    if source.type == "telegram":
        return run_telegram(index_telegram_source(db, source, progress_callback=progress_callback))

    if source.type == "local_folder":
        return index_local_source(db, source, progress_callback=progress_callback)

    raise ValueError(f"Type de source non supporte : {source.type}")
