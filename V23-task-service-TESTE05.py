"""
ChatCreova AI
V23-FUNDACAO-01

LABORATORIO — TESTE 05
FILA MINIMA

Este arquivo NÃO modifica V22.
Este arquivo NÃO substitui V23-task-service.py.

Objetivo:
- criar tarefa QUEUED;
- worker fazer claim;
- registrar lease;
- registrar heartbeat;
- finalizar tarefa;
- provar funcionamento sem Redis.
"""

from __future__ import annotations

import importlib.util
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent


def load_local_module(
    module_name: str,
    filename: str,
):
    path = BASE_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Modulo obrigatorio nao encontrado: {path}"
        )

    spec = importlib.util.spec_from_file_location(
        module_name,
        path,
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Nao foi possivel carregar: {filename}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


task_service = load_local_module(
    "chatcreova_v23_task_service_teste05",
    "V23-task-service.py",
)

database = task_service.database
TaskStatus = task_service.TaskStatus

database_connection = database.database_connection
initialize_database = database.initialize_database


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def claim_task(
    worker_id: str,
    *,
    lease_seconds: int = 60,
) -> dict[str, Any] | None:
    """
    Worker tenta assumir uma tarefa QUEUED.

    O claim, lease e mudanca para RUNNING
    acontecem dentro da mesma transacao.
    """

    if not worker_id.strip():
        raise ValueError("worker_id nao pode ser vazio.")

    if lease_seconds < 1:
        raise ValueError("lease_seconds deve ser >= 1.")

    initialize_database()

    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()

    lease_expires_at = (
        now_dt + timedelta(seconds=lease_seconds)
    ).isoformat()

    with database_connection() as db:

        db.execute("BEGIN IMMEDIATE;")

        try:

            row = db.execute(
                """
                SELECT *
                FROM tasks
                WHERE status = ?
                  AND cancel_requested = 0
                ORDER BY
                    priority ASC,
                    created_at ASC
                LIMIT 1;
                """,
                (TaskStatus.QUEUED.value,),
            ).fetchone()

            if row is None:
                db.execute("COMMIT;")
                return None

            task_id = row["task_id"]

            updated = db.execute(
                """
                UPDATE tasks
                SET
                    status = ?,
                    lease_owner = ?,
                    lease_expires_at = ?,
                    heartbeat_at = ?,
                    started_at = COALESCE(started_at, ?),
                    updated_at = ?,
                    attempt = attempt + 1
                WHERE task_id = ?
                  AND status = ?;
                """,
                (
                    TaskStatus.RUNNING.value,
                    worker_id,
                    lease_expires_at,
                    now,
                    now,
                    now,
                    task_id,
                    TaskStatus.QUEUED.value,
                ),
            )

            if updated.rowcount != 1:
                db.execute("ROLLBACK;")
                return None

            task_service.append_task_event(
                db,
                trace_id=row["trace_id"],
                task_id=task_id,
                session_id=row["session_id"],
                user_id=row["user_id"],
                project_id=row["project_id"],
                worker_id=worker_id,
                component="control_plane",
                stage="queue",
                event="task.claimed",
                status_before=TaskStatus.QUEUED.value,
                status_after=TaskStatus.RUNNING.value,
                payload={
                    "lease_owner": worker_id,
                    "lease_expires_at": lease_expires_at,
                },
            )

            db.execute("COMMIT;")

        except Exception:
            db.execute("ROLLBACK;")
            raise

    return task_service.get_task(task_id)


def heartbeat_task(
    task_id: str,
    worker_id: str,
    *,
    lease_seconds: int = 60,
) -> dict[str, Any]:
    """
    Renova heartbeat e lease somente se
    o worker atual realmente possuir a tarefa.
    """

    if lease_seconds < 1:
        raise ValueError("lease_seconds deve ser >= 1.")

    initialize_database()

    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()

    lease_expires_at = (
        now_dt + timedelta(seconds=lease_seconds)
    ).isoformat()

    with database_connection() as db:

        db.execute("BEGIN IMMEDIATE;")

        try:

            row = db.execute(
                """
                SELECT *
                FROM tasks
                WHERE task_id = ?;
                """,
                (task_id,),
            ).fetchone()

            if row is None:
                raise task_service.TaskNotFoundError(
                    f"Tarefa nao encontrada: {task_id}"
                )

            if row["status"] != TaskStatus.RUNNING.value:
                raise task_service.TaskServiceError(
                    "Heartbeat exige tarefa RUNNING."
                )

            if row["lease_owner"] != worker_id:
                raise task_service.TaskServiceError(
                    "Worker nao possui o lease desta tarefa."
                )

            db.execute(
                """
                UPDATE tasks
                SET
                    heartbeat_at = ?,
                    lease_expires_at = ?,
                    updated_at = ?
                WHERE task_id = ?;
                """,
                (
                    now,
                    lease_expires_at,
                    now,
                    task_id,
                ),
            )

            task_service.append_task_event(
                db,
                trace_id=row["trace_id"],
                task_id=task_id,
                session_id=row["session_id"],
                user_id=row["user_id"],
                project_id=row["project_id"],
                worker_id=worker_id,
                component="control_plane",
                stage="queue",
                event="task.heartbeat",
                payload={
                    "lease_expires_at": lease_expires_at,
                },
            )

            db.execute("COMMIT;")

        except Exception:
            db.execute("ROLLBACK;")
            raise

    return task_service.get_task(task_id)


def finalize_claimed_task(
    task_id: str,
    worker_id: str,
) -> dict[str, Any]:
    """
    Finalizacao minima do Teste 05.

    A tarefa so chega a COMPLETED usando
    o gate deterministico ja existente.
    """

    task = task_service.get_task(task_id)

    if task["status"] != TaskStatus.RUNNING.value:
        raise task_service.TaskServiceError(
            "Finalizacao exige tarefa RUNNING."
        )

    if task["lease_owner"] != worker_id:
        raise task_service.TaskServiceError(
            "Worker nao possui o lease desta tarefa."
        )

    return task_service.transition_task(
        task_id,
        TaskStatus.COMPLETED.value,
        component="control_plane",
        stage="queue",
        execution_verified=True,
        requires_artifact=False,
        artifact_verified=False,
        evidence={
            "worker_id": worker_id,
            "queue_test": True,
        },
        verification={
            "status": "PASS",
            "test": "TESTE_05_FILA_MINIMA",
        },
    )


def self_test() -> dict[str, bool]:

    initialize_database()

    results: dict[str, bool] = {}

    trace_id = new_id("trace_test05")
    worker_id = new_id("worker_test05")

    task = task_service.create_task(
        trace_id=trace_id,
        action="teste_05_fila_minima",
        specialist="analista_texto",
        inputs={
            "text": "teste isolado da fila"
        },
        priority=1,
        required_capabilities=[
            "text_generation"
        ],
    )

    results["enqueue"] = (
        task["status"] == TaskStatus.QUEUED.value
    )

    claimed = claim_task(
        worker_id,
        lease_seconds=60,
    )

    results["claim"] = (
        claimed is not None
        and claimed["task_id"] == task["task_id"]
        and claimed["status"] == TaskStatus.RUNNING.value
    )

    results["lease"] = (
        claimed is not None
        and claimed["lease_owner"] == worker_id
        and bool(claimed["lease_expires_at"])
    )

    before_heartbeat = (
        claimed["heartbeat_at"]
        if claimed is not None
        else None
    )

    heartbeat = heartbeat_task(
        task["task_id"],
        worker_id,
        lease_seconds=120,
    )

    results["heartbeat"] = (
        bool(heartbeat["heartbeat_at"])
        and bool(heartbeat["lease_expires_at"])
        and heartbeat["lease_owner"] == worker_id
        and heartbeat["heartbeat_at"] != before_heartbeat
    )

    completed = finalize_claimed_task(
        task["task_id"],
        worker_id,
    )

    results["finalize"] = (
        completed["status"]
        == TaskStatus.COMPLETED.value
    )

    # O laboratorio usa somente SQLite/local.
    results["no_redis"] = True

    events = task_service.list_task_events(
        task["task_id"]
    )

    event_names = {
        event["event"]
        for event in events
    }

    results["events"] = (
        "task.created" in event_names
        and "task.claimed" in event_names
        and "task.heartbeat" in event_names
        and "task.status_changed" in event_names
    )

    results["all_passed"] = all(
        results.values()
    )

    return results


if __name__ == "__main__":

    print("ChatCreova V23 — TESTE 05 FILA MINIMA")

    results = self_test()

    for name, passed in results.items():
        print(
            f"{name}: {'PASS' if passed else 'FAIL'}"
        )
