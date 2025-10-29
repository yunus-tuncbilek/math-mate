import json
import os

def load_json(folder, filename, default=""):
    full_path = os.path.join(folder, filename)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return default
    return default

def save_json(folder, filename, data=""):
    # atomic write to avoid corruption from concurrent processes
    full_path = os.path.join(folder, filename)
    tmp = full_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, full_path)