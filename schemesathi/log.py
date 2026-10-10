"""A small audit log in SQLite: every run and every tool call, with timings."""
import sqlite3
import time
from contextlib import closing

from . import config

SCHEMA = """
create table if not exists runs (id integer primary key, ts real, question text, language text, model text,
                                 status text, seconds real, retries integer, answer text);
create table if not exists events (id integer primary key, ts real, run_id integer, kind text, name text,
                                   detail text, ms real);
"""


def _conn():
    config.DATA.mkdir(exist_ok=True)
    c = sqlite3.connect(config.LOG_DB)
    c.executescript(SCHEMA)
    return c


def start(question, language) -> int:
    with closing(_conn()) as c, c:
        return c.execute("insert into runs (ts, question, language, status) values (?, ?, ?, 'running')",
                         (time.time(), question, language)).lastrowid


def finish(run_id, **fields):
    keys = ", ".join(f"{k} = ?" for k in fields)
    with closing(_conn()) as c, c:
        c.execute(f"update runs set {keys} where id = ?", (*fields.values(), run_id))


def event(run_id, kind, name, detail="", ms=None):
    try:
        with closing(_conn()) as c, c:
            c.execute("insert into events (ts, run_id, kind, name, detail, ms) values (?, ?, ?, ?, ?, ?)",
                      (time.time(), run_id, kind, name, detail, ms))
    except Exception:  # noqa: BLE001 - logging must never break the agent
        pass


def rows(sql, *args):
    with closing(_conn()) as c:
        c.row_factory = sqlite3.Row
        return [dict(r) for r in c.execute(sql, args)]
