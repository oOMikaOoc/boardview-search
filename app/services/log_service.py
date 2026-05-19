from app.models import AppLog, DownloadLog, SessionFactory


def app_log(message, level="info"):
    db = SessionFactory()
    try:
        db.add(AppLog(level=level, message=message))
        db.commit()
    finally:
        db.close()


def download_log(file_id, action, source, ip_address=None, user_agent=None):
    db = SessionFactory()
    try:
        db.add(
            DownloadLog(
                file_id=file_id,
                action=action,
                source=source,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )
        db.commit()
    finally:
        db.close()
