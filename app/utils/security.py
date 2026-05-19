from functools import wraps

from flask import Response, current_app, request


def _admin_password_configured():
    return bool(current_app.config.get("ADMIN_PASSWORD"))


def can_access_admin():
    password = current_app.config.get("ADMIN_PASSWORD", "")

    if not password:
        return True

    supplied = request.args.get("admin_password") or request.headers.get("X-Admin-Password")
    return supplied == password


def can_access_search():
    return True


def can_download_file(file_record):
    return True


def can_view_file(file_record):
    return True


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if can_access_admin():
            return view(*args, **kwargs)

        return Response("Acces admin refuse. Ajoute ?admin_password=... a l'URL.", status=403)

    return wrapper
