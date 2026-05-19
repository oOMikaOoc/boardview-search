from flask import Flask

from app.config import Config
from app.models import init_db
from app.routes.admin import admin_bp
from app.routes.files import files_bp
from app.routes.search import search_bp
from app.utils.template_filters import human_size, status_label


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    Config.ensure_directories()
    init_db()

    app.jinja_env.filters["human_size"] = human_size
    app.jinja_env.filters["status_label"] = status_label

    app.register_blueprint(search_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(admin_bp)

    return app
