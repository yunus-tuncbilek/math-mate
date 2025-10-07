import sample
from app import USERS_FILE, HOMEWORKS_FILE, INTERACTIONS_FILE   

with open(USERS_FILE, 'w') as f:
    f.write(sample.sample_users)

with open(HOMEWORKS_FILE, 'w') as f:
    f.write(sample.sample_homeworks)

with open(INTERACTIONS_FILE, 'w') as f:
    f.write(sample.sample_interactions)