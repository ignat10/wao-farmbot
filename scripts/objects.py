import shlex
from typing import Any
from screen_objects import (
    Direction,
    SwipeSpeed,
    ScreenObject,
    tap_center,
    swipe_center,
    back,
    home,
    start_app,
    close_app,
    screenshot,
    write,
    reset_screen,
)

from src.device import launch_instance
from src.utils import parse_instance
from src.objects import objects

DIRECTIONS: dict[str, Direction] = {
    "up": Direction.Up,
    "down": Direction.Down,
    "left": Direction.Left,
    "right": Direction.Right,
    "u": Direction.Up,
    "d": Direction.Down,
    "l": Direction.Left,
    "r": Direction.Right,
}

SWIPE_SPEEDS: dict[str, SwipeSpeed] = {
    "slow": SwipeSpeed.Slow,
    "normal": SwipeSpeed.Normal,
    "fast": SwipeSpeed.Fast,
    "turbo": SwipeSpeed.Turbo,
    "s": SwipeSpeed.Slow,
    "n": SwipeSpeed.Normal,
    "f": SwipeSpeed.Fast,
    "t": SwipeSpeed.Turbo,
}


def parse_value(val: str) -> Any:
    val_lower = val.lower()
    if val_lower in ("true", "yes", "t", "y"):
        return True
    if val_lower in ("false", "no", "f", "n"):
        return False
    if val_lower in ("none", "null"):
        return None
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


def parse_args_kwargs(tokens: list[str]) -> tuple[list[Any], dict[str, Any]]:
    args: list[Any] = []
    kwargs: dict[str, Any] = {}
    for token in tokens:
        if "=" in token:
            k, v = token.split("=", 1)
            kwargs[k.strip()] = parse_value(v.strip())
        else:
            args.append(parse_value(token))
    return args, kwargs


def parse_direction(val: Any) -> Direction:
    if isinstance(val, Direction):
        return val
    s = str(val).strip().lower()
    if s in DIRECTIONS:
        return DIRECTIONS[s]
    raise ValueError(f"Invalid direction '{val}'. Choose from: up, down, left, right")


def parse_speed(val: Any) -> SwipeSpeed:
    if isinstance(val, SwipeSpeed):
        return val
    s = str(val).strip().lower()
    if s in SWIPE_SPEEDS:
        return SWIPE_SPEEDS[s]
    raise ValueError(f"Invalid speed '{val}'. Choose from: slow, normal, fast, turbo")


def parse_swipe_parameters(
    args: list[Any], kwargs: dict[str, Any]
) -> tuple[Direction, SwipeSpeed, float, int | None]:
    # Support positional:
    # 1 arg: duration (defaults to Up, Turbo)
    # 2 args: dir, duration (defaults to Turbo) or speed, duration
    # 3 args: dir, speed, duration
    # 4 args: dir, speed, duration, index
    direction = kwargs.pop("dir", kwargs.pop("direction", None))
    speed = kwargs.pop("speed", None)
    duration = kwargs.pop("duration", None)
    index = kwargs.pop("index", None)

    if len(args) == 1:
        if duration is None:
            duration = float(args[0])
    elif len(args) == 2:
        if direction is None:
            try:
                direction = parse_direction(args[0])
            except ValueError:
                speed = parse_speed(args[0])
        if duration is None:
            duration = float(args[1])
    elif len(args) >= 3:
        if direction is None:
            direction = parse_direction(args[0])
        if speed is None:
            speed = parse_speed(args[1])
        if duration is None:
            duration = float(args[2])
        if len(args) >= 4 and index is None:
            index = int(args[3])

    if direction is None:
        direction = Direction.Up
    else:
        direction = parse_direction(direction)

    if speed is None:
        speed = SwipeSpeed.Turbo
    else:
        speed = parse_speed(speed)

    if duration is None:
        inp = input("Enter duration: ").strip()
        duration = float(inp)
    else:
        duration = float(duration)

    if index is not None:
        index = int(index)

    return direction, speed, duration, index


def print_help() -> None:
    print(
        """
Available commands:
  Object selection:
    <object_name>                        Select active object
    <object_name> <cmd> [args...]        Select object and run command directly
    select <object_name>                 Select object explicitly
    list [filter]                        List available objects (e.g. 'list castle')

  ScreenObject actions (run on selected object):
    exists [timeout=0.0] [index]         Check if object exists (e.g. 'exists 5', 'exists 5 index=0')
    force_exists [timeout=0.0] [index]   Require object to exist (or 'fexists')
    tap [timeout] [index] [times] [interval]
                                         Tap object (e.g. 'tap 5', 'tap times=3 interval=0.2')
    force_tap [timeout] [index] [times] [interval]
                                         Force tap (or 'ftap')
    tap_nth <index> [timeout]            Tap specific match index (e.g. 'tap_nth 1')
    spam <times> [interval=0.0] [timeout]
                                         Spam tap object (e.g. 'spam 5 0.1')
    tap_each                             Tap every match found
    count                                Count occurrences on screen
    swipe [dir] [speed] [duration] [index]
                                         Swipe on object (e.g. 'swipe up turbo 0.5', 'swipe 0.5')
    force_swipe [dir] [speed] [duration] [index]
                                         Force swipe on object (or 'fswipe')
    cal [fixed] [region] [index]         Calibrate object (e.g. 'cal fixed=true region=panel')

  Global actions:
    tap_center                           Tap center of screen
    swipe_center [dir] [speed] [duration]
                                         Swipe from center
    back                                 Android back button
    home                                 Android home button
    start_app                            Launch configured app
    close_app                            Close configured app
    write <text>                         Type text on device
    screenshot                           Take screenshot
    reset                                Reset screen cache
    help                                 Show this message
    exit / quit                          Exit script
"""
    )


def main() -> None:
    launch_instance(parse_instance())

    selected_object: ScreenObject | None = None
    selected_name: str | None = None

    while True:
        try:
            prompt = (
                f"[{selected_name}] Enter command: "
                if selected_name
                else "Enter command: "
            )
            raw_input = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not raw_input:
            continue

        try:
            parts = shlex.split(raw_input)
        except ValueError as e:
            print(f"Error parsing input: {e}")
            continue

        cmd = parts[0]
        raw_args = parts[1:]

        # Handle object selection and execution shorthand: e.g. "mail tap 5" or "mail"
        if cmd in objects and cmd not in ("back", "select", "help"):
            selected_name = cmd
            selected_object = objects[cmd]
            print(f"Selected object: {selected_name}")
            if not raw_args:
                reset_screen()
                continue
            cmd = raw_args[0]
            raw_args = raw_args[1:]

        pos_args, kwargs = parse_args_kwargs(raw_args)

        try:
            match cmd:
                case "help":
                    print_help()

                case "exit" | "quit":
                    print("Exiting.")
                    break

                case "select" | "obj":
                    if not pos_args:
                        print("Usage: select <object_name>")
                    else:
                        obj_name = str(pos_args[0])
                        if obj_name in objects:
                            selected_name = obj_name
                            selected_object = objects[obj_name]
                            print(f"Selected object: {selected_name}")
                        else:
                            print(f"Unknown object: '{obj_name}'")

                case "list":
                    pattern = str(pos_args[0]).lower() if pos_args else ""
                    matched = [
                        name for name in objects.keys() if pattern in name.lower()
                    ]
                    print(f"Found {len(matched)} object(s):")
                    print(", ".join(sorted(matched)))

                case "exists":
                    assert (
                        selected_object is not None
                    ), "exists should be called on some object"
                    timeout = float(
                        kwargs.pop("timeout", pos_args[0] if len(pos_args) > 0 else 0.0)
                    )
                    index = kwargs.pop(
                        "index", pos_args[1] if len(pos_args) > 1 else None
                    )
                    if index is not None:
                        index = int(index)
                    res = selected_object.exists(timeout=timeout, index=index, **kwargs)
                    print(res)

                case "force_exists" | "fexists":
                    assert (
                        selected_object is not None
                    ), "force_exists should be called on some object"
                    timeout = float(
                        kwargs.pop("timeout", pos_args[0] if len(pos_args) > 0 else 0.0)
                    )
                    index = kwargs.pop(
                        "index", pos_args[1] if len(pos_args) > 1 else None
                    )
                    if index is not None:
                        index = int(index)
                    res = selected_object.force_exists(
                        timeout=timeout, index=index, **kwargs
                    )
                    print("force_exists succeeded" if res is None else res)

                case "tap":
                    assert (
                        selected_object is not None
                    ), "tap should be called on some object"
                    timeout = float(
                        kwargs.pop("timeout", pos_args[0] if len(pos_args) > 0 else 0.0)
                    )
                    index = kwargs.pop(
                        "index", pos_args[1] if len(pos_args) > 1 else None
                    )
                    times = int(
                        kwargs.pop("times", pos_args[2] if len(pos_args) > 2 else 1)
                    )
                    interval = float(
                        kwargs.pop(
                            "interval", pos_args[3] if len(pos_args) > 3 else 0.0
                        )
                    )
                    if index is not None:
                        index = int(index)
                    res = selected_object.tap(
                        timeout=timeout,
                        index=index,
                        times=times,
                        interval=interval,
                        **kwargs,
                    )
                    print(res)

                case "force_tap" | "ftap":
                    assert (
                        selected_object is not None
                    ), "force_tap should be called on some object"
                    timeout = float(
                        kwargs.pop("timeout", pos_args[0] if len(pos_args) > 0 else 0.0)
                    )
                    index = kwargs.pop(
                        "index", pos_args[1] if len(pos_args) > 1 else None
                    )
                    times = int(
                        kwargs.pop("times", pos_args[2] if len(pos_args) > 2 else 1)
                    )
                    interval = float(
                        kwargs.pop(
                            "interval", pos_args[3] if len(pos_args) > 3 else 0.0
                        )
                    )
                    if index is not None:
                        index = int(index)
                    res = selected_object.force_tap(
                        timeout=timeout,
                        index=index,
                        times=times,
                        interval=interval,
                        **kwargs,
                    )
                    print("force_tap succeeded" if res is None else res)

                case "tap_nth" | "nth":
                    assert (
                        selected_object is not None
                    ), "tap_nth should be called on some object"
                    if not pos_args and "index" not in kwargs:
                        raise ValueError(
                            "tap_nth requires an index (e.g. 'tap_nth 1')"
                        )
                    index = int(kwargs.pop("index", pos_args[0]))
                    timeout = float(
                        kwargs.pop("timeout", pos_args[1] if len(pos_args) > 1 else 0.0)
                    )
                    res = selected_object.tap(timeout=timeout, index=index, **kwargs)
                    print(res)

                case "spam":
                    assert (
                        selected_object is not None
                    ), "spam should be called on some object"
                    if not pos_args and "times" not in kwargs:
                        raise ValueError("spam requires times (e.g. 'spam 5 0.1')")
                    times = int(kwargs.pop("times", pos_args[0]))
                    interval = float(
                        kwargs.pop("interval", pos_args[1] if len(pos_args) > 1 else 0.0)
                    )
                    timeout = float(
                        kwargs.pop("timeout", pos_args[2] if len(pos_args) > 2 else 0.0)
                    )
                    res = selected_object.tap(
                        times=times, interval=interval, timeout=timeout, **kwargs
                    )
                    print(res)

                case "tap_each":
                    assert (
                        selected_object is not None
                    ), "tap_each should be called on some object"
                    res = selected_object.tap_each()
                    print(f"Tapped: {res}")

                case "tap_center":
                    tap_center()

                case "swipe":
                    assert (
                        selected_object is not None
                    ), "swipe should be called on some object"
                    direction, speed, duration, index = parse_swipe_parameters(
                        pos_args, kwargs
                    )
                    res = selected_object.swipe(
                        direction, speed, duration, index=index, **kwargs
                    )
                    print(res)

                case "force_swipe" | "fswipe":
                    assert (
                        selected_object is not None
                    ), "force_swipe should be called on some object"
                    direction, speed, duration, index = parse_swipe_parameters(
                        pos_args, kwargs
                    )
                    res = selected_object.force_swipe(
                        direction, speed, duration, index=index, **kwargs
                    )
                    print("force_swipe succeeded" if res is None else res)

                case "swipe_center":
                    direction, speed, duration, _ = parse_swipe_parameters(
                        pos_args, kwargs
                    )
                    swipe_center(direction, speed, duration)

                case "cal" | "calibrate":
                    assert (
                        selected_object is not None
                    ), "calibrate should be called on some object"
                    if not pos_args and not kwargs:
                        fixed_inp = input("fixed? (y/n, default n): ").strip().lower()
                        fixed = fixed_inp in ("y", "yes", "true", "1")
                        region = input("region (default None): ").strip() or None
                        n_inp = input("index (default None): ").strip()
                        n = int(n_inp) if n_inp else None
                    else:
                        fixed = bool(
                            kwargs.pop(
                                "fixed", pos_args[0] if len(pos_args) > 0 else False
                            )
                        )
                        region = kwargs.pop(
                            "region", pos_args[1] if len(pos_args) > 1 else None
                        )
                        n = kwargs.pop(
                            "index", pos_args[2] if len(pos_args) > 2 else None
                        )
                        if region == "None":
                            region = None
                        if n is not None:
                            n = int(n)

                    selected_object.calibrate(
                        fixed=fixed, region=region, index=n, **kwargs
                    )
                    print("Calibration updated.")

                case "count":
                    assert (
                        selected_object is not None
                    ), "count should be called on some object"
                    print(selected_object.count())

                case "back":
                    back()

                case "home":
                    home()

                case "start_app":
                    start_app()

                case "close_app":
                    close_app()

                case "write":
                    text = (
                        " ".join(str(p) for p in pos_args)
                        if pos_args
                        else input("Text to write: ")
                    )
                    write(text)

                case "screenshot":
                    screenshot()

                case "reset" | "reset_screen":
                    reset_screen()

                case unknown:
                    if unknown in objects:
                        selected_name = unknown
                        selected_object = objects[unknown]
                        print(f"Selected object: {selected_name}")
                    else:
                        print(
                            f"Unknown command or object: '{unknown}'. Type 'help' for available commands."
                        )

        except Exception as e:
            print(f"Error executing '{cmd}': {e}")

        reset_screen()


if __name__ == "__main__":
    main()
