from json import load
from subprocess import run
from time import sleep

from screen_objects import device_config

from src.paths import INSTANCES_PATH


def _run_lines(command: list[str]) -> list[str]:
    return run(command, capture_output=True, text=True).stdout.strip().splitlines()


def _instances() -> set[str]:
    return set(_run_lines(["ldconsole", "list"]))


def _running_instances() -> set[str]:
    return set(_run_lines(["ldconsole", "runninglist"]))


def _devices() -> set[str]:
    return {line.split()[0].strip() for line in _run_lines(["adb", "devices"])[1:]}


def launch_instance(name: str) -> None:
    global instance_name
    assert (
        name in _instances()
    ), f"instance {name} not found in instances: {_instances()}"
    instance_name = name

    with open(INSTANCES_PATH) as file:
        serials: dict[str, str] = load(file)
        serial = serials.get(name)
        assert (
            serial is not None
        ), f"instance name {name} not found in serials: {serials} from {INSTANCES_PATH}"

    if name not in _running_instances():
        run(["ldconsole", "launch", "--name", name])
        sleep(1)
    while not serial in _devices():
        sleep(1)
    device_config(serial=serial, app="camel")
    print("loaded instance")


instance_name: str | None = None

