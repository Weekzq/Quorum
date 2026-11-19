import sqlite3

DB_PATH = "quorum.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS student (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    present INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS grp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS group_member (
    group_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS lesson (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT DEFAULT (datetime('now')),
    note TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS lesson_score (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    points INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS lesson_pick (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    picked_at TEXT DEFAULT (datetime('now'))
);
"""


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()