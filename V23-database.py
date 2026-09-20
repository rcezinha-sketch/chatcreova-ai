"""
ChatCreova AI
V23-FUNDACAO-01

DATABASE

Responsabilidades:
- SQLite local da V23
- WAL
- criação das tabelas-base
- conexão centralizada
- base para tarefas, eventos, artefatos,
  memória, sessões e uso

REGRA:
Este módulo não executa IA.
Este módulo não altera a V22.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


# ============================================================
# CAMINHOS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "V23-data"
DATABASE_PATH = DATA_DIR / "chatcreova-v23.db"


# ============================================================
# DIRETÓRIO
# ============================================================

def ensure_data_directory() -> None:
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# CONEXÃO
# ============================================================

def connect() -> sqlite3.Connection:

    ensure_data_directory()

    db = sqlite3.connect(
        DATABASE_PATH,
        timeout=30,
        isolation_level=None,
    )

    db.row_factory = sqlite3.Row

    db.execute(
        "PRAGMA journal_mode=WAL;"
    )

    db.execute(
        "PRAGMA foreign_keys=ON;"
    )

    db.execute(
        "PRAGMA busy_timeout=30000;"
    )

    return db


@contextmanager
def database_connection() -> Generator[
    sqlite3.Connection,
    None,
    None,
]:

    db = connect()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# SESSIONS
# ============================================================

CREATE_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (

    session_id TEXT PRIMARY KEY,

    user_id TEXT,

    project_id TEXT,

    status TEXT NOT NULL
        DEFAULT 'ACTIVE',

    created_at TEXT NOT NULL,

    updated_at TEXT NOT NULL,

    metadata_json TEXT NOT NULL
        DEFAULT '{}'
);
"""


# ============================================================
# TASKS
# ============================================================

CREATE_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (

    task_id TEXT PRIMARY KEY,

    trace_id TEXT NOT NULL,

    user_id TEXT,

    project_id TEXT,

    session_id TEXT,

    parent_task_id TEXT,

    specialist TEXT NOT NULL,

    specialist_version TEXT,

    action TEXT NOT NULL,

    inputs_json TEXT NOT NULL
        DEFAULT '{}',

    constraints_json TEXT NOT NULL
        DEFAULT '{}',

    priority INTEGER NOT NULL
        DEFAULT 100,

    status TEXT NOT NULL
        DEFAULT 'QUEUED',

    progress REAL NOT NULL
        DEFAULT 0,

    attempt INTEGER NOT NULL
        DEFAULT 0,

    max_attempts INTEGER NOT NULL
        DEFAULT 3,

    idempotency_key TEXT,

    required_capabilities_json TEXT
        NOT NULL
        DEFAULT '[]',

    lease_owner TEXT,

    lease_expires_at TEXT,

    heartbeat_at TEXT,

    deadline_at TEXT,

    timeout_s INTEGER,

    cancel_requested INTEGER NOT NULL
        DEFAULT 0,

    created_at TEXT NOT NULL,

    updated_at TEXT NOT NULL,

    started_at TEXT,

    finished_at TEXT,

    error_json TEXT,

    result_json TEXT,

    result_ref TEXT,

    evidence_json TEXT,

    verification_json TEXT,

    usage_json TEXT,

    schema_version INTEGER NOT NULL
        DEFAULT 1,

    created_by TEXT NOT NULL
        DEFAULT 'control_plane',

    FOREIGN KEY (session_id)
        REFERENCES sessions(session_id),

    FOREIGN KEY (parent_task_id)
        REFERENCES tasks(task_id)
);
"""


# ============================================================
# TASK EVENTS
# ============================================================

CREATE_TASK_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS task_events (

    event_id TEXT PRIMARY KEY,

    trace_id TEXT NOT NULL,

    session_id TEXT,

    user_id TEXT,

    project_id TEXT,

    task_id TEXT NOT NULL,

    attempt_id TEXT,

    artifact_id TEXT,

    worker_id TEXT,

    timestamp TEXT NOT NULL,

    stage TEXT,

    component TEXT NOT NULL,

    event TEXT NOT NULL,

    status_before TEXT,

    status_after TEXT,

    duration_ms REAL,

    error_code TEXT,

    payload_json TEXT NOT NULL
        DEFAULT '{}',

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id)
);
"""


# ============================================================
# ARTIFACTS
# ============================================================

CREATE_ARTIFACTS_TABLE = """
CREATE TABLE IF NOT EXISTS artifacts (

    artifact_id TEXT PRIMARY KEY,

    user_id TEXT,

    project_id TEXT,

    source_task_id TEXT NOT NULL,

    producer TEXT NOT NULL,

    type TEXT NOT NULL,

    mime TEXT,

    version INTEGER NOT NULL
        DEFAULT 1,

    storage_location TEXT,

    storage_backend TEXT NOT NULL
        DEFAULT 'local',

    size_bytes INTEGER,

    hash TEXT,

    hash_algorithm TEXT
        DEFAULT 'sha256',

    status TEXT NOT NULL
        DEFAULT 'PENDING',

    verify_status TEXT NOT NULL
        DEFAULT 'NOT_VERIFIED',

    verified_at TEXT,

    metadata_json TEXT NOT NULL
        DEFAULT '{}',

    created_at TEXT NOT NULL,

    created_by TEXT NOT NULL
        DEFAULT 'control_plane',

    parent_artifacts_json TEXT NOT NULL
        DEFAULT '[]',

    supersedes_artifact_id TEXT,

    visibility TEXT NOT NULL
        DEFAULT 'private',

    access_scope TEXT,

    immutable INTEGER NOT NULL
        DEFAULT 1,

    expires_at TEXT,

    retention TEXT,

    usage_json TEXT,

    preview_ref TEXT,

    FOREIGN KEY (source_task_id)
        REFERENCES tasks(task_id),

    FOREIGN KEY (supersedes_artifact_id)
        REFERENCES artifacts(artifact_id)
);
"""


# ============================================================
# MEMORY
# ============================================================

CREATE_MEMORY_TABLE = """
CREATE TABLE IF NOT EXISTS memory_records (

    memory_id TEXT PRIMARY KEY,

    scope TEXT NOT NULL,

    user_id TEXT,

    project_id TEXT,

    session_id TEXT,

    specialist TEXT,

    task_id TEXT,

    memory_type TEXT NOT NULL,

    key TEXT,

    value_json TEXT NOT NULL,

    provenance_json TEXT NOT NULL
        DEFAULT '{}',

    promoted_by TEXT NOT NULL,

    created_at TEXT NOT NULL,

    updated_at TEXT NOT NULL,

    active INTEGER NOT NULL
        DEFAULT 1
);
"""


# ============================================================
# USAGE EVENTS
# ============================================================

CREATE_USAGE_TABLE = """
CREATE TABLE IF NOT EXISTS usage_events (

    event_id TEXT PRIMARY KEY,

    task_id TEXT,

    user_id TEXT,

    project_id TEXT,

    trace_id TEXT,

    resource_type TEXT NOT NULL,

    unit TEXT NOT NULL,

    quantity REAL NOT NULL,

    timestamp TEXT NOT NULL,

    metadata_json TEXT NOT NULL
        DEFAULT '{}',

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id)
);
"""


# ============================================================
# ÍNDICES
# ============================================================

INDEXES = (

    """
    CREATE INDEX IF NOT EXISTS
    idx_tasks_status_priority
    ON tasks(
        status,
        priority,
        created_at
    );
    """,

    """
    CREATE INDEX IF NOT EXISTS
    idx_tasks_trace
    ON tasks(trace_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS
    idx_tasks_project
    ON tasks(project_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS
    idx_events_task
    ON task_events(
        task_id,
        timestamp
    );
    """,

    """
    CREATE INDEX IF NOT EXISTS
    idx_events_trace
    ON task_events(
        trace_id,
        timestamp
    );
    """,

    """
    CREATE INDEX IF NOT EXISTS
    idx_artifacts_task
    ON artifacts(source_task_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS
    idx_memory_scope
    ON memory_records(
        scope,
        user_id,
        project_id
    );
    """,

    """
    CREATE INDEX IF NOT EXISTS
    idx_usage_task
    ON usage_events(
        task_id,
        timestamp
    );
    """,
)


# ============================================================
# INICIALIZAÇÃO
# ============================================================

def initialize_database() -> None:

    ensure_data_directory()

    with database_connection() as db:

        db.execute("BEGIN;")

        try:

            db.execute(
                CREATE_SESSIONS_TABLE
            )

            db.execute(
                CREATE_TASKS_TABLE
            )

            db.execute(
                CREATE_TASK_EVENTS_TABLE
            )

            db.execute(
                CREATE_ARTIFACTS_TABLE
            )

            db.execute(
                CREATE_MEMORY_TABLE
            )

            db.execute(
                CREATE_USAGE_TABLE
            )

            for statement in INDEXES:
                db.execute(statement)

            db.execute("COMMIT;")

        except Exception:

            db.execute("ROLLBACK;")
            raise


# ============================================================
# HEALTH
# ============================================================

def database_health() -> dict:

    try:

        initialize_database()

        with database_connection() as db:

            version = db.execute(
                """
                SELECT sqlite_version()
                AS version;
                """
            ).fetchone()

            journal = db.execute(
                """
                PRAGMA journal_mode;
                """
            ).fetchone()

            tables = db.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name;
                """
            ).fetchall()

        return {
            "ok": True,
            "database": "sqlite",
            "sqlite_version": (
                version["version"]
            ),
            "journal_mode": journal[0],
            "path": str(
                DATABASE_PATH
            ),
            "tables": [
                row["name"]
                for row in tables
            ],
        }

    except Exception as exc:

        return {
            "ok": False,
            "database": "sqlite",
            "error": (
                type(exc).__name__
            ),
        }


# ============================================================
# TESTE ISOLADO
# ============================================================

if __name__ == "__main__":

    initialize_database()

    print(
        "ChatCreova V23 Database"
    )

    print(
        database_health()
    )
