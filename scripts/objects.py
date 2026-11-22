import shlex
from screen_objects import (
    SwipeSpeed,
    ScreenObject,
    tap_center,
    back,
    reset_screen,
)
from src.device import launch_instance
from src.utils import parse_instance
from src.objects import objects

launch_instance(parse_instance())

selected_object: ScreenObject | None = None
selected_name: str | None = None


def print_help():
    print(
        """Commands:
  <object_name>                      - select object (or 'select <name>')
  exists [timeout=0.0] [index]       - check existence (e.g. exists 5)
  tap [timeout=0.0] [index] [times]  - tap object (e.g. tap 5, tap 0 1, tap 0 None 5)
  swipe [dir] [speed] [dur] [index]  - swipe (e.g. swipe up turbo 0.5 or swipe 0.5)
  cal [fixed] [region] [index]       - calibrate (e.g. cal true)
  count                              - count matching objects on screen
  tap_each                           - tap every match found
  tap_center                         - tap center of screen
  back                               - back button
  reset                              - reset screen cache
  list [filter]                      - list available objects (e.g. list castle)
  help / exit                        - show help / exit
"""
    )


while True:
    try:
        prompt = f"[{selected_name}] > " if selected_name else "> "
        cmd_line = input(prompt).strip()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
        break

    if not cmd_line:
        continue

    parts = shlex.split(cmd_line)
    cmd, args = parts[0], parts[1:]

    # Select object directly by name: e.g. "mail" or "mail tap 5"
    if cmd in objects:
        selected_name = cmd
        selected_object = objects[cmd]
        print(f"Selected object: {selected_name}")
        if not args:
            reset_screen()
            continue
        cmd, args = args[0], args[1:]

    try:
        match cmd:
            case "help":
                print_help()

            case "exit" | "quit":
                break

            case "select" if args:
                name = args[0]
                if name in objects:
                    selected_name = name
                    selected_object = objects[name]
                    print(f"Selected object: {selected_name}")
                else:
                    print(f"Object '{name}' not found")

            case "list":
                flt = args[0].lower() if args else ""
                found = [k for k in objects if flt in k.lower()]
                print(f"Found ({len(found)}): {', '.join(sorted(found))}")

            case "exists":
                assert selected_object is not None, "Select an object first"
                t = float(args[0]) if len(args) > 0 else 0.0
                idx = int(args[1]) if len(args) > 1 and args[1] != "None" else None
                print(selected_object.exists(timeout=t, index=idx))

            case "tap":
                assert selected_object is not None, "Select an object first"
                t = float(args[0]) if len(args) > 0 else 0.0
                idx = int(args[1]) if len(args) > 1 and args[1] != "None" else None
                times = int(args[2]) if len(args) > 2 else 1
                interval = float(args[3]) if len(args) > 3 else 0.0
                print(
                    selected_object.tap(
                        timeout=t, index=idx, times=times, interval=interval
                    )
                )

            case "swipe":
                assert selected_object is not None, "Select an object first"
                if len(args) == 1:
                    d = 0.0
                    spd = SwipeSpeed.Turbo
                    dur = float(args[0])
                    idx = None
                else:
                    d = (
                        getattr(SwipeSpeed, args[0].lower().capitalize(), 0.0)
                        if len(args) > 0
                        else 0.0
                    )
                    spd = (
                        getattr(SwipeSpeed, args[1].lower(), SwipeSpeed.Fast)
                        if len(args) > 1
                        else SwipeSpeed.Fast
                    )
                    dur = float(args[2]) if len(args) > 2 else 1.0
                    idx = int(args[3]) if len(args) > 3 else None
                print(selected_object.swipe(d, spd, dur, index=idx))

            case "cal":
                assert selected_object is not None, "Select an object first"
                fixed = (
                    args[0].lower() in ("true", "1", "yes")
                    if len(args) > 0
                    else False
                )
                region = (
                    args[1]
                    if len(args) > 1 and args[1].lower() != "none"
                    else None
                )
                idx = int(args[2]) if len(args) > 2 else None
                selected_object.calibrate(fixed=fixed, region=region, index=idx)
                print("Calibrated")

            case "count":
                assert selected_object is not None, "Select an object first"
                print(selected_object.count())

            case "tap_each":
                assert selected_object is not None, "Select an object first"
                print(selected_object.tap_each())

            case "tap_center":
                tap_center()

            case "back":
                back()

            case "reset":
                reset_screen()

            case _:
                print(f"Unknown command '{cmd}'. Type 'help' for commands.")

    except Exception as e:
        print(f"Error: {e}")

    reset_screen()
