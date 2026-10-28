from os import makedirs
import logging
from datetime import datetime

from src.paths import LOGS_DIR
from src.device import instance_name


makedirs(LOGS_DIR, exist_ok=True)

timestamp = datetime.now().strftime("%d-%m-%Y-%H.%M")

log_filename = LOGS_DIR / f"{instance_name}-{timestamp}.log"

logger = logging.getLogger("MyApp")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%d-%b-%Y %H:%M:%S")

file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
