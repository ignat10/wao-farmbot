import argparse

from tabulate import tabulate

from src.castles import (
    add_castle,
    get_castle,
    get_column,
    remove_all_castles,
    remove_castle,
    update_castle,
    DATA_COLUMNS,
)

def print_castles_table() -> None:
    castles = sorted(
        [get_castle(name) for name in get_column("name")],
        key=lambda castle: (
            castle["google"],
            castle["account"] if castle["account"] is not None else -1,
        ),
    )
    print(tabulate(castles, headers="keys", tablefmt="rounded_outline"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage castles.")
    parser.add_argument(
        "action",
        nargs="?",
        type=str.lower,
        choices=["add", "edit", "remove", "remove-all", "list"],
        help="Action to perform (add/edit/remove/remove-all/list)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show all stored data when listing castles",
    )
    args = parser.parse_args()

    command = (
        args.action
        if args.action is not None
        else input("Action (add/edit/remove/remove-all/list): ").strip().lower()
    )
    match command:
        case "add":
            name = input("Castle name: ").strip()
            google = int(input("Google: "))
            add_castle(name, google)
            print(f"Added castle: {name}")
        case "edit":
            name = input("Castle name: ").strip()
            column = input(f"Field {DATA_COLUMNS}: ").strip().lower()
            value = input(f"New {column}: ")
            update_castle(name, column, value)
            print(f"Updated {name}: {column} = {value}")
        case "remove":
            name = input("Castle name: ").strip()
            remove_castle(name)
            print(f"Removed castle: {name}")
        case "remove-all":
            confirmation = input("Delete ALL castles? Type DELETE to confirm: ").strip()
            if confirmation == "DELETE":
                deleted_count = remove_all_castles()
                print(f"Removed {deleted_count} castles")
            else:
                print("Cancelled")
        case "list":
            names = sorted(get_column("name"))
            if not names:
                print("No castles found.")
            elif args.verbose:
                print_castles_table()
            else:
                for idx, name in enumerate(names, 1):
                    print(f"  {idx}. {name}")
                print(f"\nTotal: {len(names)} castles\n")


if __name__ == "__main__":
    main()
