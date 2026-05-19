from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, scoped_session, sessionmaker

from app.config import Config

engine = create_engine(f"sqlite:///{Config.DATABASE_PATH}", connect_args={"check_same_thread": False})
SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
SessionLocal = scoped_session(SessionFactory)
Base = declarative_base()


def utcnow():
    return datetime.utcnow()


class TimestampMixin:
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False, default="telegram")
    name = Column(String(255), nullable=False)
    identifier = Column(String(500), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    max_messages_to_scan = Column(Integer, nullable=True)
    last_indexed_at = Column(DateTime, nullable=True)

    files = relationship("File", back_populates="source", cascade="all, delete-orphan")


class File(Base, TimestampMixin):
    __tablename__ = "files"
    __table_args__ = (
        UniqueConstraint("source_id", "telegram_message_id", name="uq_source_message"),
    )

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    source_type = Column(String(50), nullable=False)
    telegram_channel_id = Column(String(255), nullable=True)
    telegram_message_id = Column(Integer, nullable=True)
    telegram_document_id = Column(String(255), nullable=True)
    remote_unique_id = Column(String(500), nullable=True)
    title = Column(String(500), nullable=True)
    filename = Column(String(500), nullable=False)
    normalized_filename = Column(String(500), nullable=False, index=True)
    extension = Column(String(50), nullable=True, index=True)
    mime_type = Column(String(255), nullable=True)
    size = Column(Integer, nullable=True)
    message_date = Column(DateTime, nullable=True)
    caption = Column(Text, nullable=True)
    downloaded = Column(Boolean, default=False, nullable=False)
    local_path = Column(String(1000), nullable=True)
    hash = Column(String(64), nullable=True, index=True)
    downloaded_at = Column(DateTime, nullable=True)

    source = relationship("Source", back_populates="files")


class Setting(Base, TimestampMixin):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    is_secret = Column(Boolean, default=False, nullable=False)


class DownloadLog(Base):
    __tablename__ = "download_logs"

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=True)
    action = Column(String(50), nullable=False)
    source = Column(String(50), nullable=False)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class AppLog(Base):
    __tablename__ = "app_logs"

    id = Column(Integer, primary_key=True)
    level = Column(String(20), nullable=False, default="info")
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


def init_db():
    Base.metadata.create_all(bind=engine)
    seed_default_sources()


def seed_default_sources():
    db = SessionLocal()
    try:
        for identifier in [item.strip() for item in Config.DEFAULT_TELEGRAM_CHANNELS.split(",") if item.strip()]:
            existing = db.query(Source).filter_by(type="telegram", identifier=identifier).first()
            if not existing:
                db.add(Source(type="telegram", name=identifier, identifier=identifier, enabled=True))

        storage_path = str(Config.STORAGE_PATH)
        download_sources = db.query(Source).filter_by(type="local_folder", name="Download").order_by(Source.id.asc()).all()
        download_source = download_sources[0] if download_sources else None
        if download_source:
            download_source.identifier = storage_path
            download_source.enabled = True
            for duplicate in download_sources[1:]:
                db.delete(duplicate)

        if not download_source:
            download_source = db.query(Source).filter_by(type="local_folder", identifier=storage_path).first()

        if not download_source:
            db.add(
                Source(
                    type="local_folder",
                    name="Download",
                    identifier=storage_path,
                    enabled=True,
                )
            )

        db.commit()
    finally:
        db.close()


def db_session():
    return SessionLocal()
