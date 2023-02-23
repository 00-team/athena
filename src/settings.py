
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATABASE_PATH = BASE_DIR / 'data/database.json'

# EXPIRE_TIME = 6 * 60 * 60
EXPIRE_TIME = 7


with open(BASE_DIR / 'secrets.json') as f:
    SECRETS = json.load(f)
