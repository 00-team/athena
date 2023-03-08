
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'

# make the data dir if not exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

USER_DB_PATH = DATA_DIR / 'users.json'
CHANNEL_DB_PATH = DATA_DIR / 'channels.json'
GENERAL_DB_PATH = DATA_DIR / 'generals.json'


EXPIRE_TIME = 15 * 60
FORWARD_DELAY = 10 * 60

with open(BASE_DIR / 'secrets.json') as f:
    SECRETS = json.load(f)
