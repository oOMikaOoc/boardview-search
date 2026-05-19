import os

from app.models import Setting


SECRET_KEYS = {"TELEGRAM_API_HASH", "ADMIN_PASSWORD", "SECRET_KEY"}


def get_setting(db, key, default=None):
    env_value = os.getenv(key)

    if env_value not in (None, ""):
        return env_value

    setting = db.query(Setting).filter_by(key=key).first()
    if setting and setting.value not in (None, ""):
        return setting.value

    return default


def set_setting(db, key, value, is_secret=None):
    setting = db.query(Setting).filter_by(key=key).first()

    if not setting:
        setting = Setting(key=key)
        db.add(setting)

    setting.value = value
    setting.is_secret = key in SECRET_KEYS if is_secret is None else is_secret
    db.commit()
    return setting


def masked_status(db, key):
    value = get_setting(db, key, "")
    if not value:
        return "non configure"
    return "configure"


def telegram_config(db):
    return {
        "api_id": get_setting(db, "TELEGRAM_API_ID", ""),
        "api_hash": get_setting(db, "TELEGRAM_API_HASH", ""),
        "session_name": get_setting(db, "TELEGRAM_SESSION_NAME", "telegram_session"),
    }
