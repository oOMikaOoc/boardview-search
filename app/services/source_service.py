from app.config import Config
from app.models import Source, utcnow


def source_limit(source):
    return source.max_messages_to_scan or Config.DEFAULT_TELEGRAM_SEARCH_LIMIT


def active_sources(db, source_type=None):
    query = db.query(Source).filter_by(enabled=True)

    if source_type:
        query = query.filter_by(type=source_type)

    return query.order_by(Source.name.asc()).all()


def touch_indexed(db, source):
    source.last_indexed_at = utcnow()
    db.commit()
