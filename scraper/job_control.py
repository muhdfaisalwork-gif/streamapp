"""
job_control.py — Prevents the exact failure mode this project hit three times
in one night: two ingestion processes (or a stale one left over from a crash)
writing to catalog.db at once, and long-running jobs losing all progress when
the process dies mid-run (power outage, zombie process, etc).

job_locks ensures only one live process can hold a given job name at a time —
a lock older than stale_after_seconds is assumed to belong to a dead process
and can be reclaimed. job_checkpoints lets a job record its own progress and
resume from there instead of restarting from zero.

Generated with qwen2.5-coder:7b via Ollama MCP, assembled and bug-fixed by
Claude (the draft's LockedJob class never exposed a heartbeat() method despite
being the whole point of keeping a live lock refreshed during a long run).
"""
from __future__ import annotations
import json
import os
import sqlite3
import time


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS job_locks (
            job_name TEXT PRIMARY KEY,
            pid INTEGER NOT NULL,
            started_at INTEGER NOT NULL,
            heartbeat_at INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS job_checkpoints (
            job_name TEXT PRIMARY KEY,
            cursor_json TEXT NOT NULL,
            updated_at INTEGER NOT NULL
        )
    """)
    conn.commit()


def acquire_lock(conn: sqlite3.Connection, job_name: str, stale_after_seconds: int = 300) -> bool:
    ensure_tables(conn)
    now = int(time.time())
    row = conn.execute("SELECT pid, heartbeat_at FROM job_locks WHERE job_name = ?", (job_name,)).fetchone()

    if row is None:
        conn.execute(
            "INSERT INTO job_locks (job_name, pid, started_at, heartbeat_at) VALUES (?, ?, ?, ?)",
            (job_name, os.getpid(), now, now),
        )
        conn.commit()
        return True

    _, heartbeat_at = row
    if now - heartbeat_at > stale_after_seconds:
        conn.execute(
            "UPDATE job_locks SET pid = ?, started_at = ?, heartbeat_at = ? WHERE job_name = ?",
            (os.getpid(), now, now, job_name),
        )
        conn.commit()
        return True

    return False


def release_lock(conn: sqlite3.Connection, job_name: str) -> None:
    conn.execute("DELETE FROM job_locks WHERE job_name = ?", (job_name,))
    conn.commit()


def heartbeat(conn: sqlite3.Connection, job_name: str) -> None:
    conn.execute("UPDATE job_locks SET heartbeat_at = ? WHERE job_name = ?", (int(time.time()), job_name))
    conn.commit()


def save_checkpoint(conn: sqlite3.Connection, job_name: str, data: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO job_checkpoints (job_name, cursor_json, updated_at) VALUES (?, ?, ?)",
        (job_name, json.dumps(data), int(time.time())),
    )
    conn.commit()


def load_checkpoint(conn: sqlite3.Connection, job_name: str) -> dict | None:
    row = conn.execute("SELECT cursor_json FROM job_checkpoints WHERE job_name = ?", (job_name,)).fetchone()
    return json.loads(row[0]) if row else None


class LockedJob:
    def __init__(self, conn: sqlite3.Connection, job_name: str, stale_after_seconds: int = 300):
        self.conn = conn
        self.job_name = job_name
        self.stale_after_seconds = stale_after_seconds
        self.acquired = False

    def __enter__(self) -> "LockedJob":
        self.acquired = acquire_lock(self.conn, self.job_name, self.stale_after_seconds)
        return self

    def __exit__(self, exc_type, exc_value, tb) -> None:
        if self.acquired:
            release_lock(self.conn, self.job_name)

    def heartbeat(self) -> None:
        heartbeat(self.conn, self.job_name)

    def save_checkpoint(self, data: dict) -> None:
        save_checkpoint(self.conn, self.job_name, data)

    def load_checkpoint(self) -> dict | None:
        return load_checkpoint(self.conn, self.job_name)
