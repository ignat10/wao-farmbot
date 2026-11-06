from json import load
from time import perf_counter

from src.device import launch_instance
from src.utils import parse_instance
from src.objects import objects

launch_instance(parse_instance())

screencap_timer = perf_counter()
objects.values().__iter__().__next__().exists()  # screencap
screencap = perf_counter() - screencap_timer

with open("data/objects.json") as f:
    data = load(f)
assert isinstance(data, dict)

fixed_elapsed = unfixed_elapsed = 0.0


def exists_all():
    global fixed_elapsed, unfixed_elapsed
    for name, obj in objects.items():
        start = perf_counter()
        obj.exists()
        end = perf_counter()
        delta = end - start
        if data[name][0] is None:  # if coords are not fixed:
            unfixed_elapsed += delta
        else:
            fixed_elapsed += delta


exists_all()
fixed_load, unfixed_load = fixed_elapsed, unfixed_elapsed
fixed_elapsed = unfixed_elapsed = 0.0
exists_all()
load = fixed_load - fixed_elapsed + unfixed_load - unfixed_elapsed

print(
    f"fixed took {fixed_elapsed:2f}. not fixed: {unfixed_elapsed:2f}, load: {load:2f}, screencap: {screencap:2f}"
)
