from threading import Lock, Thread
from uuid import uuid4

from app.models import db_session
from app.routes_presenters import file_result
from app.services.log_service import app_log
from app.services.search_service import global_search

jobs = {}
jobs_lock = Lock()


def _set_job(job_id, **updates):
    with jobs_lock:
        job = jobs[job_id]
        job.update(updates)
        return dict(job)


def _progress(job_id, payload):
    source = payload.get("source", "")
    scanned = payload.get("scanned", 0)
    limit = payload.get("limit", 0)
    indexed = payload.get("indexed", 0)

    if payload.get("type") == "source_start":
        detail = f"Preparation source : {source}"
    elif payload.get("type") == "telegram":
        detail = f"Telegram : {source} - message {scanned} / {limit}, {indexed} fichier(s) indexes"
    elif payload.get("type") == "local_folder":
        detail = f"Dossier local : {source} - fichier {scanned} / {limit}"
    else:
        detail = "Recherche dans la base locale"

    percent = int((scanned / limit) * 100) if limit else 0
    _set_job(job_id, detail=detail, percent=max(0, min(percent, 100)))


def _run_search(job_id, query, mode, reindex):
    db = db_session()
    try:
        _set_job(job_id, status="running", detail="Preparation de la recherche", percent=0)
        local_only = mode == "local"
        app_log(f"Recherche effectuee : {query} mode={mode} reindex={reindex}")
        results = [
            file_result(file_record)
            for file_record in global_search(
                db,
                query,
                progress_callback=lambda payload: _progress(job_id, payload),
                local_only=local_only,
                reindex=reindex,
            )
        ]
        _set_job(job_id, status="done", detail=f"Recherche terminee : {len(results)} resultat(s)", percent=100, results=results)
    except Exception as e:
        app_log(f"Erreur recherche : {e}", level="error")
        _set_job(job_id, status="error", detail=str(e), error=str(e), percent=100)
    finally:
        db.close()


def start_search_job(query, mode="all", reindex=False):
    job_id = uuid4().hex
    with jobs_lock:
        jobs[job_id] = {
            "id": job_id,
            "query": query,
            "mode": mode,
            "reindex": reindex,
            "status": "queued",
            "detail": "Recherche en attente",
            "percent": 0,
            "results": [],
            "error": None,
        }

    thread = Thread(target=_run_search, args=(job_id, query, mode, reindex), daemon=True)
    thread.start()
    return job_id


def get_search_job(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        return dict(job) if job else None
