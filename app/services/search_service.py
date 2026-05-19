from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from app.models import File, Source
from app.services.index_service import index_source
from app.services.log_service import app_log
from app.utils.normalization import normalize_filename
from app.utils.storage import existing_local_path


def split_terms(query):
    return [normalize_filename(term) for term in query.split() if term.strip()]


def matches_terms_query(terms):
    conditions = []

    for term in terms:
        pattern = f"%{term}%"
        conditions.append(or_(File.normalized_filename.like(pattern), File.caption.like(pattern), File.title.like(pattern)))

    return conditions


def search_database(db, query, local_only=False):
    terms = split_terms(query)

    if not terms:
        return []

    query_obj = db.query(File).options(selectinload(File.source))

    if local_only:
        query_obj = (
            query_obj.outerjoin(Source)
            .filter(
                or_(
                    Source.type == "local_folder",
                    File.downloaded.is_(True),
                    File.local_path.isnot(None),
                )
            )
        )

    for condition in matches_terms_query(terms):
        query_obj = query_obj.filter(condition)

    results = query_obj.order_by(File.message_date.desc().nullslast(), File.updated_at.desc()).limit(300).all()

    if local_only:
        return [file_record for file_record in results if existing_local_path(file_record)]

    return results


def refresh_enabled_sources(db, progress_callback=None, local_only=False):
    sources = db.query(Source).filter_by(enabled=True)

    if local_only:
        sources = sources.filter_by(type="local_folder")

    sources = sources.all()

    for source in sources:
        source_name = source.name
        try:
            if progress_callback:
                progress_callback({"source": source_name, "type": "source_start", "scanned": 0, "limit": 1, "indexed": 0})
            index_source(db, source, progress_callback=progress_callback)
        except Exception as e:
            app_log(f"Erreur indexation {source_name} : {e}", level="error")


def global_search(db, query, progress_callback=None, local_only=False, reindex=False):
    if reindex:
        refresh_enabled_sources(db, progress_callback=progress_callback, local_only=local_only)
    if progress_callback:
        progress_callback({"source": "Base locale", "type": "database", "scanned": 1, "limit": 1, "indexed": 0})
    results = search_database(db, query, local_only=local_only)
    seen = set()
    deduped = []

    for file_record in results:
        key = (
            file_record.source_id,
            file_record.telegram_message_id,
            file_record.remote_unique_id,
            file_record.telegram_document_id,
            file_record.normalized_filename,
            file_record.size,
        )

        if key in seen:
            continue

        seen.add(key)
        deduped.append(file_record)

    return deduped
