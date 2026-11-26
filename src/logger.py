import logging
from datetime import datetime
from src.paths import LOGS_DIR

logger = logging.getLogger("MyApp")
logger.setLevel(logging.INFO)


def setup_logger(instance_name: str) -> None:
    if logger.handlers:
        return

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%d-%m-%Y-%H.%M")
    log_filename = LOGS_DIR / f"{instance_name}-{timestamp}.log"

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")

    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
