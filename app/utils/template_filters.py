def human_size(size):
    if not size:
        return ""

    units = ["o", "Ko", "Mo", "Go", "To"]
    value = float(size)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024

    return f"{size} o"


def status_label(file_record):
    if file_record.downloaded and file_record.local_path:
        return "local disponible"
    return "distant indexe"
