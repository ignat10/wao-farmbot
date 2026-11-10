from sqlite3 import Connection, IntegrityError, Row, connect
from time import perf_counter
from typing import Any, Iterator, TYPE_CHECKING

from src.paths import CASTLES_DB_PATH


if TYPE_CHECKING:
    from src.actions import Castle

DATA_COLUMNS = frozenset({"name", "last_login", "google", "account", "avatar"})


def _connect() -> Connection:
    connection = connect(CASTLES_DB_PATH, timeout=30)
    connection.row_factory = Row
    connection.execute("PRAGMA busy_timeout = 30000")
    return connection


def get_castle(name: str) -> dict[str, Any]:
    with _connect() as connection:
        row = connection.execute(
            f"SELECT {', '.join(DATA_COLUMNS)} FROM castles WHERE name = ?",
            (name,),
        ).fetchone()
    if row is None:
        raise KeyError(f"unknown castle: {name}")
    return dict(row)  # type: ignore


def get_column(column: str) -> list[Any]:
    if column not in DATA_COLUMNS:
        raise ValueError(f"unknown castle column: {column}")
    with _connect() as connection:
        return [row[0] for row in connection.execute(f"SELECT {column} FROM castles")]


def get_accounts_in_google(google: int) -> int:
    with _connect() as connection:
        return connection.execute(
            f"SELECT COUNT(*) AS count FROM castles WHERE account IS NOT NULL AND google = {google};"
        ).fetchone()[0]


def get_castle_name_by_avatar(avatar_number: int) -> str | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT name FROM castles WHERE avatar = ? ORDER BY name LIMIT 1",
            (avatar_number,),
        ).fetchone()
    return row[0] if row is not None else None


def update_castle(name: str, column: str, value: Any) -> None:
    if column not in DATA_COLUMNS:
        raise ValueError(f"unknown castle column: {column}")
    with _connect() as connection:
        cursor = connection.execute(
            f"UPDATE castles SET {column} = ? WHERE name = ?",
            (value, name),
        )
    if cursor.rowcount != 1:
        raise KeyError(f"unknown castle: {name}")


def add_castle(name: str, google: int) -> None:
    if not name:
        raise ValueError("castle name cannot be empty")

    try:
        with _connect() as connection:
            connection.execute(
                "INSERT INTO castles (name, google, is_busy) VALUES (?, ?, 0)",
                (name, google),
            )
    except IntegrityError as error:
        raise ValueError(f"castle already exists: {name}") from error


def remove_castle(name: str) -> None:
    with _connect() as connection:
        cursor = connection.execute(
            "DELETE FROM castles WHERE name = ?",
            (name,),
        )

        if cursor.rowcount != 1:
            raise KeyError(f"unknown castle: {name}")


def remove_all_castles() -> int:
    """Delete every castle and return the number of deleted records."""
    with _connect() as connection:
        cursor = connection.execute("DELETE FROM castles")
    return cursor.rowcount


def iter_castles() -> Iterator[Castle]:
    from src.actions import Castle
    while (name := get_available()) is not None:
        castle = Castle(**get_castle(name))
        started_at = perf_counter()
        yield castle

        seconds = int(perf_counter() - started_at)
        minutes, seconds = divmod(seconds, 60)
        elapsed = f"{minutes}m {seconds}s"
        print(f"Castle {name} took {elapsed}")

    print("No available castles.")


def get_available() -> str | None:
    """Get a free castle busy. Return None if there is no free castle."""
    with _connect() as connection:
        row = connection.execute("""
            UPDATE castles
            SET is_busy = 1, last_login = CURRENT_TIMESTAMP
            WHERE name = (
                SELECT name
                FROM castles
                WHERE is_busy = 0
                ORDER BY
                    CASE WHEN account IS NULL THEN 0 ELSE 1 END ASC,
                    last_login ASC
                LIMIT 1
            )
            RETURNING name
            """).fetchone()

        return row[0] if row is not None else None


def release(name: str) -> None:
    with _connect() as connection:
        cursor = connection.execute(
            "UPDATE castles SET is_busy = 0 WHERE name = ?",
            (name,),
        )

    if cursor.rowcount == 0:
        raise KeyError(f"unknown castle: {name}")


def release_all() -> None:
    """Release every castle before starting a new group of workers."""
    with _connect() as connection:
        connection.execute("UPDATE castles SET is_busy = 0")
