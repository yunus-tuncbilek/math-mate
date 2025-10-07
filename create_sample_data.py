import sample

USERS_FILE = "users.json"
HOMEWORKS_FILE = "homeworks.json"
INTERACTIONS_FILE = "interactions.json"

with open(USERS_FILE, 'w') as f:
    f.write(sample.sample_users)

with open(HOMEWORKS_FILE, 'w') as f:
    f.write(sample.sample_hws)

with open(INTERACTIONS_FILE, 'w') as f:
    f.write(sample.sample_interactions)