import json
import os
import sample

USERS_FILE = "users.json"
HOMEWORKS_FILE = "homeworks.json"
INTERACTIONS_FILE = "interactions.json"

def save_json(filename, data):
    # atomic write to avoid corruption from concurrent processes
    tmp = filename + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, filename)

save_json(USERS_FILE, json.loads(sample.sample_users))
save_json(HOMEWORKS_FILE, json.loads(sample.sample_homeworks))
save_json(INTERACTIONS_FILE, json.loads(sample.sample_interactions))