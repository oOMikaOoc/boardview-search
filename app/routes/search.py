from flask import Blueprint, jsonify, render_template, request, url_for

from app.models import db_session
from app.routes_presenters import file_result
from app.services.log_service import app_log
from app.services.search_jobs import get_search_job, start_search_job
from app.services.search_service import global_search
from app.utils.security import can_access_search

search_bp = Blueprint("search", __name__)


@search_bp.route("/")
def index():
    if not can_access_search():
        return "Acces refuse", 403

    query = request.args.get("q", "").strip()
    mode = request.args.get("mode", "all")
    reindex = request.args.get("reindex") == "1"
    results = []
    error = None

    if query:
        db = db_session()
        try:
            app_log(f"Recherche effectuee : {query}")
            results = [
                file_result(file_record)
                for file_record in global_search(db, query, local_only=mode == "local", reindex=reindex)
            ]
        except Exception as e:
            error = str(e)
            app_log(f"Erreur recherche : {e}", level="error")
        finally:
            db.close()

    return render_template("search/index.html", query=query, mode=mode, reindex=reindex, results=results, error=error)


@search_bp.route("/search/start", methods=["POST"])
def search_start():
    if not can_access_search():
        return jsonify({"error": "Acces refuse"}), 403

    query = request.form.get("q", "").strip()
    mode = request.form.get("mode", "all")
    reindex = request.form.get("reindex") == "1"
    if not query:
        return jsonify({"error": "Recherche vide"}), 400

    job_id = start_search_job(query, mode=mode, reindex=reindex)
    return jsonify({"job_id": job_id, "status_url": url_for("search.search_status", job_id=job_id)})


@search_bp.route("/search/status/<job_id>")
def search_status(job_id):
    job = get_search_job(job_id)

    if not job:
        return jsonify({"error": "Recherche introuvable"}), 404

    return jsonify(job)
