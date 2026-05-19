import asyncio

from telethon import TelegramClient

from app.config import Config
from app.models import db_session
from app.services.settings_service import telegram_config


async def main():
    Config.ensure_directories()
    db = db_session()
    try:
        config = telegram_config(db)

        if not config["api_id"] or not config["api_hash"]:
            raise SystemExit("Configure TELEGRAM_API_ID et TELEGRAM_API_HASH dans .env ou dans /admin/settings.")

        session_path = Config.TELEGRAM_SESSION_PATH / (config["session_name"] or "telegram_session")
        client = TelegramClient(str(session_path), int(config["api_id"]), config["api_hash"])

        await client.start()
        me = await client.get_me()
        print(f"Session Telegram connectee : {getattr(me, 'username', None) or me.id}")
        await client.disconnect()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
