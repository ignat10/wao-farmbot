from os import getenv
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


_ROOT_DIR = Path(__file__).parent.parent
_DATA_DIR = _ROOT_DIR / "data"
_ASSETS_DIR = _ROOT_DIR / "assets"

LOGS_DIR = _ROOT_DIR / "logs"
SAMPLES_DIR = _ASSETS_DIR / "samples"
REGIONS_DIR = _ASSETS_DIR / "regions"
INSTANCES_PATH = _DATA_DIR / "instances.json"
CASTLES_DB_PATH = _DATA_DIR / "castles.db"

if (p := getenv("DOCKER_IMAGE")) is not None:
    DOCKER_IMAGE_DIR = Path(p)
else:
    raise ValueError("Not found DOCKER_IMAGE field in .env file.")

if (p := getenv("REDROID")) is not None:
    REDROID_DIR = Path(p)
else:
    raise ValueError("Not found REDROID field in .env file.")

WAO_APK_PATH = Path(p) if (p := getenv("WAO_APK")) is not None else None
