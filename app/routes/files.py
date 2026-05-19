import os
import sys
from pathlib import Path

from flask import Blueprint, Response, abort, jsonify, request, send_file

from app.models import File, db_session
from app.services.log_service import app_log, download_log
from app.services.telegram_service import download_file, run_telegram
from app.utils.security import can_download_file, can_view_file
from app.utils.storage import existing_local_path, is_viewable, mimetype_for

files_bp = Blueprint("files", __name__)


def ensure_local_file(db, file_record):
    local_path = existing_local_path(file_record)

    if local_path:
        return local_path, "local"

    if file_record.downloaded and file_record.local_path:
        app_log(f"Chemin local manquant pour {file_record.filename}", level="warning")

    if file_record.source_type == "local_folder":
        raise ValueError("Fichier local indexe mais absent du disque.")

    path = run_telegram(download_file(db, file_record))
    return path, file_record.source_type


@files_bp.route("/download/<int:file_id>")
def download(file_id):
    db = db_session()
    try:
        file_record = db.query(File).filter_by(id=file_id).first()

        if not file_record:
            abort(404, "Fichier introuvable.")

        if not can_download_file(file_record):
            abort(403, "Telechargement refuse.")

        path, source = ensure_local_file(db, file_record)
        download_log(file_record.id, "download", source, request.remote_addr, request.user_agent.string)
        app_log(f"Fichier servi en telechargement : {file_record.filename}")
        return send_file(path, as_attachment=True, download_name=file_record.filename, mimetype=mimetype_for(file_record))
    except Exception as e:
        app_log(f"Erreur telechargement : {e}", level="error")
        return Response(f"Erreur telechargement : {e}", status=500)
    finally:
        db.close()


@files_bp.route("/fetch/<int:file_id>", methods=["POST"])
def fetch(file_id):
    db = db_session()
    try:
        file_record = db.query(File).filter_by(id=file_id).first()

        if not file_record:
            return jsonify({"error": "Fichier introuvable."}), 404

        if not can_download_file(file_record):
            return jsonify({"error": "Telechargement refuse."}), 403

        path, source = ensure_local_file(db, file_record)
        download_log(file_record.id, "fetch", source, request.remote_addr, request.user_agent.string)
        app_log(f"Fichier stocke localement : {file_record.filename}")

        viewable = is_viewable(file_record)
        return jsonify(
            {
                "ok": True,
                "file_id": file_record.id,
                "filename": file_record.filename,
                "status": "local disponible",
                "action_label": "Voir",
                "action_url": f"/view/{file_record.id}" if viewable else f"/open-folder/{file_record.id}",
                "action_kind": "view" if viewable else "open_folder",
                "local_path": str(path),
            }
        )
    except Exception as e:
        app_log(f"Erreur recuperation : {e}", level="error")
        return jsonify({"error": f"Erreur recuperation : {e}"}), 500
    finally:
        db.close()


@files_bp.route("/view/<int:file_id>")
def view(file_id):
    db = db_session()
    try:
        file_record = db.query(File).filter_by(id=file_id).first()

        if not file_record:
            abort(404, "Fichier introuvable.")

        if not can_view_file(file_record):
            abort(403, "Affichage refuse.")

        if not is_viewable(file_record):
            return Response("Ce type de fichier ne peut pas etre affiche dans le navigateur.", status=415)

        path, source = ensure_local_file(db, file_record)
        download_log(file_record.id, "view", source, request.remote_addr, request.user_agent.string)
        app_log(f"Fichier affiche : {file_record.filename}")
        return send_file(path, as_attachment=False, download_name=file_record.filename, mimetype=mimetype_for(file_record))
    except Exception as e:
        app_log(f"Erreur affichage : {e}", level="error")
        return Response(f"Erreur affichage : {e}", status=500)
    finally:
        db.close()


@files_bp.route("/open-folder/<int:file_id>", methods=["GET", "POST"])
def open_folder(file_id):
    db = db_session()
    try:
        file_record = db.query(File).filter_by(id=file_id).first()

        if not file_record:
            abort(404, "Fichier introuvable.")

        if not can_view_file(file_record):
            abort(403, "Ouverture refusee.")

        path, source = ensure_local_file(db, file_record)
        path = Path(path)

        if sys.platform.startswith("win"):
            os.startfile(path.parent)
            message = f"Dossier ouvert : {path.parent}"
        else:
            message = f"Fichier local : {path}"

        download_log(file_record.id, "open_folder", source, request.remote_addr, request.user_agent.string)
        app_log(message)
        if request.headers.get("X-Requested-With") == "fetch":
            return jsonify({"ok": True, "message": message})
        return Response(message, mimetype="text/plain")
    except Exception as e:
        app_log(f"Erreur ouverture dossier : {e}", level="error")
        return Response(f"Erreur ouverture dossier : {e}", status=500)
    finally:
        db.close()
