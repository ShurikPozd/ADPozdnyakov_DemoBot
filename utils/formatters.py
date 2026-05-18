def format_time(seconds):
    if seconds is None:
        return "?"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"