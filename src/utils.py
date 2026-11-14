from argparse import ArgumentParser
from typing import NoReturn

from screen_objects import screenshot, start_app


def log_raise(msg: str) -> NoReturn:
    screenshot()
    raise RuntimeError(f"{msg} Check screen.png for more details.")


def parse_instance() -> str:
    parser = ArgumentParser()
    parser.add_argument("instance", help="LDPlayer instance name")
    instance = parser.parse_args().instance
    assert instance is not None, f"required instance name"
    assert isinstance(instance, str)
    return instance


def start_game() -> None:
    start_app(["-e", "unity", "-force-gles"])
