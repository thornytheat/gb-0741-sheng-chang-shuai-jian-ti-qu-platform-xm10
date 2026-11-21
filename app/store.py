import sqlite3
from contextlib import contextmanager

from fastapi import Request

SCHEMA = '''
CREATE TABLE IF NOT EXISTS source (id TEXT PRIMARY KEY, content BLOB NOT NULL);
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES source(id), version TEXT NOT NULL,
  created_at TEXT NOT NULL, elapsed_ms INTEGER NOT NULL, digest TEXT NOT NULL, evidence BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS runs_recent ON runs(created_at DESC);
'''


class Store:
    def __init__(self, path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute('PRAGMA journal_mode = WAL')
            connection.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys = ON')
        try:
            with connection:
                yield connection
        finally:
            connection.close()


def get_store(request: Request) -> Store:
    return request.app.state.store
