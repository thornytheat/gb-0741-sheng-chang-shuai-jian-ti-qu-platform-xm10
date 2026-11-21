import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
SAMPLES = {key: APP_DIR.parent / 'sample_data' / f'{key}.csv' for key in ('hall', 'reference')}
BAND_CENTRES = (63, 125, 250, 500, 1000, 2000, 4000, 8000)
MAX_BYTES = 8 * 1024 * 1024
MAX_ROWS = 100_000
RULE_VERSION = 'rt-schroeder-1'


def database_path():
    return Path(os.environ.get('DECAY_DB', 'measurements.sqlite3'))
