from __future__ import annotations

from enum import Enum

from src.objects import objects, resources_need, avatars
from src.utils import log_raise


class MineType(Enum):
    IRON = objects["iron_type"]
    STONE = objects["stone_type"]
    WOOD = objects["wood_type"]
    FOOD = objects["food_type"]

    @classmethod
    def check_need(cls) -> MineType | None:
        for mine in MineType:
            if mine == MineType.IRON: # HACK: remove when need_iron template captured
                continue
            if resources_need[mine.name.lower()].exists():
                return mine
        return None


class Task(Enum):
    UPGRADE = objects["start_upgrading"]
    POWER = objects["battle_power"]
    RECRUIT = objects["recruit_"]
    SCOUT = objects["scout"]
    CONQUER = objects["conquer"]
    GATHER = objects["gather_task"]
    RUINS = objects["ruins_wave_3"]

    @classmethod
    def check(cls) -> Task | None:
        for task in cls:
            if task.value.exists():
                return task
        return None

def check_avatar() -> int | None:
    for num, avatar in avatars.items():
        if avatar.exists():
            return num

    if objects['pause'].exists():
        return None

    log_raise("Loaded, but no avatar was found.")
