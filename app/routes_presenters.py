from app.utils.storage import existing_local_path, is_viewable


def telegram_message_url(file_record, source):
    if file_record.source_type != "telegram" or not source or not file_record.telegram_message_id:
        return None

    identifier = (source.identifier or "").strip().lstrip("@")

    if not identifier or identifier.startswith("-") or identifier.isdigit():
        return None

    return f"https://t.me/{identifier}/{file_record.telegram_message_id}"


def file_result(file_record):
    source = file_record.source
    local_available = existing_local_path(file_record) is not None
    viewable = is_viewable(file_record)

    if not local_available:
        action_label = "DL"
        action_url = f"/fetch/{file_record.id}"
        action_kind = "fetch"
    elif viewable:
        action_label = "Voir"
        action_url = f"/view/{file_record.id}"
        action_kind = "view"
    else:
        action_label = "Voir"
        action_url = f"/open-folder/{file_record.id}"
        action_kind = "open_folder"

    return {
        "id": file_record.id,
        "filename": file_record.filename,
        "extension": file_record.extension,
        "source_type": file_record.source_type,
        "source_name": source.name if source else "",
        "downloaded": file_record.downloaded,
        "local_path": file_record.local_path,
        "size": file_record.size,
        "message_date": file_record.message_date,
        "caption": file_record.caption or "",
        "local_available": local_available,
        "viewable": viewable,
        "action_label": action_label,
        "action_url": action_url,
        "action_kind": action_kind,
        "telegram_message_id": file_record.telegram_message_id,
        "telegram_url": telegram_message_url(file_record, source),
        "status": "local disponible" if local_available else "distant indexe",
    }
