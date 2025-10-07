import sample
import app

with open(app.USERS_FILE, 'w') as f:
    f.write(sample.sample_users)

with open(app.HOMEWORKS_FILE, 'w') as f:
    f.write(sample.sample_homeworks)

with open(app.INTERACTIONS_FILE, 'w') as f:
    f.write(sample.sample_interactions)