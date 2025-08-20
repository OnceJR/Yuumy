"""SQLite database helper for the multistream recorder.

This module defines a thin wrapper around ``aiosqlite`` to handle
initialisation of the database and provide convenience methods for
executing queries.  The database stores information about recorded
sessions, stream metadata and user preferences.  Schema evolution can
be extended as the project develops.
"""

import asyncio
from pathlib import Path
from typing import Any, Iterable, Optional, Tuple

import aiosqlite


class Database:
    """Asynchronous SQLite helper class."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._db: Optional[aiosqlite.Connection] = None

    async def initialise(self) -> None:
        """Initialises the database connection and creates tables if needed."""
        self._db = await aiosqlite.connect(self._path)
        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                status TEXT NOT NULL,
                file_path TEXT,
                quality TEXT,
                error_message TEXT
            );
            """
        )
        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        await self._db.commit()

    async def execute(self, query: str, params: Iterable[Any] = ()) -> None:
        assert self._db is not None
        await self._db.execute(query, params)
        await self._db.commit()

    async def fetchall(self, query: str, params: Iterable[Any] = ()) -> Iterable[Tuple]:
        assert self._db is not None
        cursor = await self._db.execute(query, params)
        rows = await cursor.fetchall()
        await cursor.close()
        return rows

    async def fetchone(self, query: str, params: Iterable[Any] = ()) -> Optional[Tuple]:
        assert self._db is not None
        cursor = await self._db.execute(query, params)
        row = await cursor.fetchone()
        await cursor.close()
        return row

    async def close(self) -> None:
        if self._db:
            await self._db.close()