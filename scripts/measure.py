from pprint import pprint
from time import perf_counter

from screen_objects import reset_screen

from src.device import launch_instance
from src.utils import parse_instance
from src.objects import objects

launch_instance(parse_instance())

template = next(iter(objects.values()))
template.exists()
reset_screen()

screencaps = 10
screencaps_time = 0
for _ in range(screencaps):
    start = perf_counter()
    template.exists()
    end = perf_counter()
    template.exists()
    after = perf_counter()
    reset_screen()
    screencaps_time += (end - start) - (after - end)

screencap = screencaps_time / screencaps


def exists_all() -> tuple[set[str], float]:
    found = set()
    start = perf_counter()
    for name, obj in objects.items():
        if obj.exists():
            found.add(name)
    elapsed = perf_counter() - start
    return found, elapsed


existing_objects, total_elapsed = exists_all()

print("Existing objects:")
pprint(existing_objects)
print(
    f"\ntotal took: {total_elapsed:.2f}s, screencap: {screencap:.2f}s"
)
