from flask import Blueprint, abort, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import distinct, func

from app.models import AppLog, DownloadLog, File, Source, db_session
from app.services.cleanup_service import clean_missing_local_files
from app.services.index_service import index_source as dispatch_index_source
from app.services.settings_service import masked_status, set_setting, telegram_config
from app.services.source_service import source_limit
from app.services.telegram_service import complete_login, message_count, run_telegram, send_login_code, test_connection
from app.utils.security import require_admin

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_url(endpoint, **values):
    password = request.args.get("admin_password")
    if password:
        values["admin_password"] = password
    return url_for(endpoint, **values)


@admin_bp.context_processor
def inject_admin_helpers():
    return {"admin_url": admin_url, "source_limit": source_limit}


def indexed_message_count(db, source):
    if not source or source.type != "telegram":
        return None

    return (
        db.query(func.count(distinct(File.telegram_message_id)))
        .filter(
            File.source_id == source.id,
            File.source_type == "telegram",
            File.telegram_message_id.isnot(None),
        )
        .scalar()
        or 0
    )


@admin_bp.route("/")
@require_admin
def dashboard():
    db = db_session()
    try:
        stats = {
            "sources": db.query(Source).count(),
            "active_sources": db.query(Source).filter_by(enabled=True).count(),
            "files": db.query(File).count(),
            "downloaded": db.query(File).filter_by(downloaded=True).count(),
        }
        latest_files = db.query(File).order_by(File.updated_at.desc()).limit(10).all()
        latest_downloads = db.query(DownloadLog).order_by(DownloadLog.created_at.desc()).limit(10).all()
        errors = db.query(AppLog).filter_by(level="error").order_by(AppLog.created_at.desc()).limit(10).all()
        return render_template("admin/dashboard.html", stats=stats, latest_files=latest_files, latest_downloads=latest_downloads, errors=errors)
    finally:
        db.close()


@admin_bp.route("/settings", methods=["GET", "POST"])
@require_admin
def settings():
    db = db_session()
    notice = None
    try:
        if request.method == "POST":
            for key in ["TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_SESSION_NAME"]:
                value = request.form.get(key, "").strip()
                if value:
                    set_setting(db, key, value)
            notice = "Parametres enregistres."

        statuses = {key: masked_status(db, key) for key in ["TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_SESSION_NAME"]}
        config = telegram_config(db)
        config["api_hash"] = ""
        return render_template("admin/settings.html", statuses=statuses, config=config, notice=notice)
    finally:
        db.close()


@admin_bp.route("/telegram/test")
@require_admin
def telegram_test():
    db = db_session()
    try:
        result = run_telegram(test_connection(db))
        return render_template("admin/telegram_test.html", result=result)
    finally:
        db.close()


@admin_bp.route("/sources")
@require_admin
def sources():
    db = db_session()
    try:
        items = db.query(Source).order_by(Source.created_at.desc()).all()
        return render_template("admin/sources.html", sources=items)
    finally:
        db.close()


@admin_bp.route("/sources/add", methods=["GET", "POST"])
@require_admin
def source_add():
    db = db_session()
    try:
        if request.method == "POST":
            source = Source(
                type=request.form["type"].strip(),
                name=request.form["name"].strip(),
                identifier=request.form["identifier"].strip(),
                enabled=bool(request.form.get("enabled")),
                max_messages_to_scan=int(request.form["max_messages_to_scan"] or 0) or None,
            )
            db.add(source)
            db.commit()
            return redirect(admin_url("admin.sources"))

        return render_template(
            "admin/source_form.html",
            source=None,
            telegram_count=None,
            telegram_indexed_count=None,
            telegram_coverage=None,
            telegram_count_error=None,
        )
    finally:
        db.close()


@admin_bp.route("/sources/<int:source_id>/edit", methods=["GET", "POST"])
@require_admin
def source_edit(source_id):
    db = db_session()
    telegram_count = None
    telegram_indexed_count = None
    telegram_coverage = None
    telegram_count_error = None
    try:
        source = db.query(Source).filter_by(id=source_id).first()
        if not source:
            abort(404)

        if request.method == "POST":
            source.name = request.form["name"].strip()
            source.type = request.form["type"].strip()
            source.identifier = request.form["identifier"].strip()
            source.enabled = bool(request.form.get("enabled"))
            source.max_messages_to_scan = int(request.form["max_messages_to_scan"] or 0) or None
            db.commit()
            return redirect(admin_url("admin.sources"))

        if source.type == "telegram":
            telegram_indexed_count = indexed_message_count(db, source)
            try:
                telegram_count = run_telegram(message_count(db, source.identifier))
            except Exception as e:
                telegram_count_error = str(e)

            if telegram_count:
                telegram_coverage = round((telegram_indexed_count / telegram_count) * 100, 1)

        return render_template(
            "admin/source_form.html",
            source=source,
            telegram_count=telegram_count,
            telegram_indexed_count=telegram_indexed_count,
            telegram_coverage=telegram_coverage,
            telegram_count_error=telegram_count_error,
        )
    finally:
        db.close()


@admin_bp.route("/telegram/message-count")
@require_admin
def telegram_message_count():
    identifier = request.args.get("identifier", "").strip()
    if not identifier:
        return jsonify({"error": "Identifiant Telegram vide."}), 400

    db = db_session()
    try:
        count = run_telegram(message_count(db, identifier))
        return jsonify({"ok": True, "identifier": identifier, "count": count})
    except Exception as e:
        app_log(f"Erreur comptage Telegram {identifier} : {e}", level="error")
        return jsonify({"error": f"Comptage impossible : {e}"}), 500
    finally:
        db.close()


@admin_bp.route("/sources/<int:source_id>/toggle")
@require_admin
def source_toggle(source_id):
    db = db_session()
    try:
        source = db.query(Source).filter_by(id=source_id).first()
        if not source:
            abort(404)
        source.enabled = not source.enabled
        db.commit()
        return redirect(admin_url("admin.sources"))
    finally:
        db.close()


@admin_bp.route("/sources/<int:source_id>/delete")
@require_admin
def source_delete(source_id):
    db = db_session()
    try:
        source = db.query(Source).filter_by(id=source_id).first()
        if not source:
            abort(404)
        db.delete(source)
        db.commit()
        return redirect(admin_url("admin.sources"))
    finally:
        db.close()


@admin_bp.route("/sources/<int:source_id>/index")
@require_admin
def source_index(source_id):
    db = db_session()
    try:
        source = db.query(Source).filter_by(id=source_id).first()
        if not source:
            abort(404)
        result = dispatch_index_source(db, source)
        return render_template("admin/source_index.html", source=source, result=result)
    finally:
        db.close()


@admin_bp.route("/cleanup/local")
@require_admin
def cleanup_local():
    db = db_session()
    try:
        result = clean_missing_local_files(db)
        return render_template("admin/cleanup.html", result=result)
    finally:
        db.close()


@admin_bp.route("/telegram/login", methods=["GET", "POST"])
@require_admin
def telegram_login():
    db = db_session()
    error = None
    notice = None
    try:
        if request.method == "POST":
            phone = request.form["phone"].strip()
            result = run_telegram(send_login_code(db, phone))
            if result["ok"]:
                session["telegram_login_phone"] = phone
                session["telegram_phone_code_hash"] = result["phone_code_hash"]
                return redirect(admin_url("admin.telegram_verify"))
            error = result.get("error", "Impossible d'envoyer le code.")

        return render_template("admin/telegram_login.html", error=error, notice=notice)
    finally:
        db.close()


@admin_bp.route("/telegram/verify", methods=["GET", "POST"])
@require_admin
def telegram_verify():
    db = db_session()
    error = None
    result = None
    phone = session.get("telegram_login_phone")
    phone_code_hash = session.get("telegram_phone_code_hash")

    try:
        if not phone or not phone_code_hash:
            return redirect(admin_url("admin.telegram_login"))

        if request.method == "POST":
            code = request.form["code"].strip()
            password = request.form.get("password", "").strip() or None
            result = run_telegram(complete_login(db, phone, code, phone_code_hash, password=password))

            if result.get("ok"):
                session.pop("telegram_login_phone", None)
                session.pop("telegram_phone_code_hash", None)
            elif result.get("needs_password"):
                error = result["error"]
            else:
                error = result.get("error", "Connexion Telegram impossible.")

        return render_template("admin/telegram_verify.html", phone=phone, error=error, result=result)
    finally:
        db.close()
