from __future__ import annotations

from enum import Enum

from screen_objects import ScreenObject

from src.objects import (
    objects,
    resources_need,
    avatars,
    castle_levels,
    march_limits,
    castle_ui_elements,
    kingroad_tasks,
)
from src.utils import log_raise


class TemplateMatcher[T]:
    """Matches screen templates against a mapped set of keys to detect visible UI elements."""

    def __init__(self, mapping: dict[T, ScreenObject]):
        self._mapping = mapping

    def check(self) -> T | None:
        """Returns the first matching key whose ScreenObject exists on screen, or None."""
        for key, obj in self._mapping.items():
            if obj.exists():
                return key
        return None

    def find_all(self) -> set[T]:
        """Returns a set of all keys whose ScreenObjects currently exist on screen."""
        return {
            key
            for key, obj in self._mapping.items()
            if obj.exists()
        }

    def get_missing(self) -> set[T]:
        """Returns a set of keys whose ScreenObjects are not found on screen."""
        return set(self._mapping.keys()) - self.find_all()

    def exactly_one(self) -> T:
        """Returns the key if exactly one object exists; raises an error if multiple or None match"""
        found = self.find_all()
        length = len(found)
        if length == 1:
            return found.pop()
        else:
            log_raise(f"Expected exactly one element, but {length} were found: {found if length != 0 else ''}")

    def __getitem__(self, key: T) -> ScreenObject:
        return self._mapping[key]

    def __contains__(self, key: object) -> bool:
        return key in self._mapping

    def __len__(self) -> int:
        return len(self._mapping)


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

castle_levels_matcher = TemplateMatcher(castle_levels)
march_limits_matcher = TemplateMatcher(march_limits)
avatars_matcher = TemplateMatcher(avatars)
castle_ui_matcher = TemplateMatcher(castle_ui_elements)
tasks_matcher = TemplateMatcher(kingroad_tasks)


def check_avatar() -> int | None:
    if (avatar_num := avatars_matcher.check()) is not None:
        return avatar_num

    if objects['pause'].exists() or objects['lord_avatar'].exists():
        return None

    log_raise("Loaded, but no avatar was found.")
