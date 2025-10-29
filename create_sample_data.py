import os
from app_utils import save_json, load_json

sample_data_folder = "sample_data"
USERS_FILE = "users.json"
HOMEWORKS_FILE = "homeworks.json"
INTERACTIONS_FILE = "interactions.json"

data_folder = "data"
os.makedirs(data_folder, exist_ok=True)

save_json(data_folder, USERS_FILE, load_json(sample_data_folder, USERS_FILE))

# escape backslashes so LaTeX like \sum, \int don't produce invalid JSON escapes
data = load_json(sample_data_folder, HOMEWORKS_FILE)
save_json(data_folder, HOMEWORKS_FILE, data)

data = load_json(sample_data_folder, INTERACTIONS_FILE)
save_json(data_folder, INTERACTIONS_FILE, data)