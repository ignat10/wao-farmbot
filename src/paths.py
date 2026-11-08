from pathlib import Path

_ROOT_DIR = Path(__file__).parent.parent
_DATA_DIR = _ROOT_DIR / "data"
_ASSETS_DIR = _ROOT_DIR / "assets"

LOGS_DIR = _ROOT_DIR / "logs"
SAMPLES_DIR = _ASSETS_DIR / "samples"
REGIONS_DIR = _ASSETS_DIR / "regions"
INSTANCES_PATH = _DATA_DIR / "instances.json"
CASTLES_DB_PATH = _DATA_DIR / "castles.db"
