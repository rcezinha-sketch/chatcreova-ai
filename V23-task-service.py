"""
ChatCreova AI
V23-FUNDACAO-01

Task Service

Responsabilidades:
- criar tarefas;
- persistir tarefas no SQLite;
- registrar eventos;
- consultar tarefas;
- solicitar cancelamento;
- controlar transições através da máquina de estados;
- impedir conclusão sem evidência.

IMPORTANTE:
Este módulo NÃO executa IA.
Este módulo NÃO chama Ollama.
Este módulo NÃO modifica V22.
"""

from __future__ import annotations

import importlib.util
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ============================================================
# CARREGAMENTO DOS MÓDULOS V23
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


def load_local_module(
    module_name: str,
    filename: str,
):
    """
    Carrega um módulo V23 pelo nome físico do arquivo.

    Usamos isso porque os arquivos atuais possuem hífen
    no nome, por exemplo:

    V23-database.py
    V23-task-state.py

    Hífens não funcionam em imports Python normais.
    """

    path = BASE_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Módulo obrigatório não encontrado: {path}"
        )

    spec = importlib.util.spec_from_file_location(
        module_name,
        path,
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Não foi possível carregar: {filename}"
        )

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


database = load_local_module(
    "chatcreova_v23_database",
    "V23-database.py",
)

task_state = load_local_module(
    "chatcreova_v23_task_state",
    "V23-task-state.py",
)


# ============================================================
# ATALHOS CONTROLADOS
# ============================================================

database_connection = database.database_connection
initialize_database = database.initialize_database

TaskStatus = task_state.TaskStatus
TaskStateError = task_state.TaskStateError
authorize_transition = task_state.authorize_transition


# ============================================================
# UTILITÁRIOS
# ============================================================

def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def new_id(prefix: str) -> str:
    return (
        f"{prefix}_"
        f"{uuid.uuid4().hex}"
    )


def json_dump(
    value: Any,
) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def json_load(
    value: str | None,
    default: Any,
) -> Any:

    if value is None:
        return default

    try:
        return json.loads(value)

    except (
        json.JSONDecodeError,
        TypeError,
    ):
        return default


# ============================================================
# EXCEÇÕES DO SERVIÇO
# ============================================================

class TaskServiceError(Exception):
    """Erro-base do serviço de tarefas."""


class TaskNotFoundError(TaskServiceError):
    """Tarefa não encontrada."""


class DuplicateIdempotencyError(TaskServiceError):
    """Idempotency key já utilizada."""


class TaskPersistenceError(TaskServiceError):
    """Falha de persistência."""


# ============================================================
# SERIALIZAÇÃO DE TAREFA
# ============================================================

def task_row_to_dict(
    row,
) -> dict[str, Any]:

    return {
        "task_id": row["task_id"],
        "trace_id": row["trace_id"],
        "user_id": row["user_id"],
        "project_id": row["project_id"],
        "session_id": row["session_id"],
        "parent_task_id": row["parent_task_id"],
        "specialist": row["specialist"],
        "specialist_version": (
            row["specialist_version"]
        ),
        "action": row["action"],
        "inputs": json_load(
            row["inputs_json"],
            {},
        ),
        "constraints": json_load(
            row["constraints_json"],
            {},
        ),
        "priority": row["priority"],
        "status": row["status"],
        "progress": row["progress"],
        "attempt": row["attempt"],
        "max_attempts": row["max_attempts"],
        "idempotency_key": (
            row["idempotency_key"]
        ),
        "required_capabilities": json_load(
            row["required_capabilities_json"],
            [],
        ),
        "lease_owner": row["lease_owner"],
        "lease_expires_at": (
            row["lease_expires_at"]
        ),
        "heartbeat_at": row["heartbeat_at"],
        "deadline_at": row["deadline_at"],
        "timeout_s": row["timeout_s"],
        "cancel_requested": bool(
            row["cancel_requested"]
        ),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "started_at": row["started_at"],
        "finished_at": row["finished_at"],
        "error": json_load(
            row["error_json"],
            None,
        ),
        "result": json_load(
            row["result_json"],
            None,
        ),
        "result_ref": row["result_ref"],
        "evidence": json_load(
            row["evidence_json"],
            None,
        ),
        "verification": json_load(
            row["verification_json"],
            None,
        ),
        "usage": json_load(
            row["usage_json"],
            None,
        ),
        "schema_version": (
            row["schema_version"]
        ),
        "created_by": row["created_by"],
    }


# ============================================================
# EVENTOS
# ============================================================

def append_task_event(
    db,
    *,
    trace_id: str,
    task_id: str,
    component: str,
    event: str,
    session_id: str | None = None,
    user_id: str | None = None,
    project_id: str | None = None,
    attempt_id: str | None = None,
    artifact_id: str | None = None,
    worker_id: str | None = None,
    stage: str | None = None,
    status_before: str | None = None,
    status_after: str | None = None,
    duration_ms: float | None = None,
    error_code: str | None = None,
    payload: dict[str, Any] | None = None,
) -> str:
    """
    Registra evento append-only.
    """

    event_id = new_id("evt")

    db.execute(
        """
        INSERT INTO task_events (
            event_id,
            trace_id,
            session_id,
            user_id,
            project_id,
            task_id,
            attempt_id,
            artifact_id,
            worker_id,
            timestamp,
            stage,
            component,
            event,
            status_before,
            status_after,
            duration_ms,
            error_code,
            payload_json
        )
        VALUES (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?
        );
        """,
        (
            event_id,
            trace_id,
            session_id,
            user_id,
            project_id,
            task_id,
            attempt_id,
            artifact_id,
            worker_id,
            utc_now(),
            stage,
            component,
            event,
            status_before,
            status_after,
            duration_ms,
            error_code,
            json_dump(payload or {}),
        ),
    )

    return event_id


# ============================================================
# CONSULTA
# ============================================================

def get_task(
    task_id: str,
) -> dict[str, Any]:

    initialize_database()

    with database_connection() as db:

        row = db.execute(
            """
            SELECT *
            FROM tasks
            WHERE task_id = ?;
            """,
            (task_id,),
        ).fetchone()

    if row is None:
        raise TaskNotFoundError(
            f"Tarefa não encontrada: {task_id}"
        )

    return task_row_to_dict(row)


def list_task_events(
    task_id: str,
) -> list[dict[str, Any]]:

    initialize_database()

    with database_connection() as db:

        rows = db.execute(
            """
            SELECT *
            FROM task_events
            WHERE task_id = ?
            ORDER BY timestamp ASC;
            """,
            (task_id,),
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# IDEMPOTÊNCIA
# ============================================================

def find_by_idempotency_key(
    idempotency_key: str,
) -> dict[str, Any] | None:

    initialize_database()

    with database_connection() as db:

        row = db.execute(
            """
            SELECT *
            FROM tasks
            WHERE idempotency_key = ?
            ORDER BY created_at DESC
            LIMIT 1;
            """,
            (idempotency_key,),
        ).fetchone()

    if row is None:
        return None

    return task_row_to_dict(row)


# ============================================================
# CRIAÇÃO DE TAREFA
# ============================================================

def create_task(
    *,
    trace_id: str,
    action: str,
    specialist: str = "analista_texto",
    specialist_version: str = "v1",
    user_id: str | None = None,
    project_id: str | None = None,
    session_id: str | None = None,
    parent_task_id: str | None = None,
    inputs: dict[str, Any] | None = None,
    constraints: dict[str, Any] | None = None,
    priority: int = 100,
    max_attempts: int = 3,
    idempotency_key: str | None = None,
    required_capabilities: (
        list[str] | None
    ) = None,
    deadline_at: str | None = None,
    timeout_s: int | None = None,
    created_by: str = "control_plane",
) -> dict[str, Any]:
    """
    Cria uma tarefa QUEUED.

    Não executa a tarefa.
    """

    if not action.strip():
        raise ValueError(
            "action não pode ser vazio."
        )

    if not specialist.strip():
        raise ValueError(
            "specialist não pode ser vazio."
        )

    if priority < 0:
        raise ValueError(
            "priority não pode ser negativo."
        )

    if max_attempts < 1:
        raise ValueError(
            "max_attempts deve ser >= 1."
        )

    initialize_database()

    if idempotency_key:

        existing = find_by_idempotency_key(
            idempotency_key
        )

        if existing is not None:
            return existing

    task_id = new_id("task")
    now = utc_now()

    inputs = inputs or {}
    constraints = constraints or {}
    required_capabilities = (
        required_capabilities
        or ["text_generation"]
    )

    with database_connection() as db:

        db.execute("BEGIN;")

        try:

            db.execute(
                """
                INSERT INTO tasks (
                    task_id,
                    trace_id,
                    user_id,
                    project_id,
                    session_id,
                    parent_task_id,
                    specialist,
                    specialist_version,
                    action,
                    inputs_json,
                    constraints_json,
                    priority,
                    status,
                    progress,
                    attempt,
                    max_attempts,
                    idempotency_key,
                    required_capabilities_json,
                    deadline_at,
                    timeout_s,
                    cancel_requested,
                    created_at,
                    updated_at,
                    schema_version,
                    created_by
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?
                );
                """,
                (
                    task_id,
                    trace_id,
                    user_id,
                    project_id,
                    session_id,
                    parent_task_id,
                    specialist,
                    specialist_version,
                    action,
                    json_dump(inputs),
                    json_dump(constraints),
                    priority,
                    TaskStatus.QUEUED.value,
                    0,
                    0,
                    max_attempts,
                    idempotency_key,
                    json_dump(
                        required_capabilities
                    ),
                    deadline_at,
                    timeout_s,
                    0,
                    now,
                    now,
                    1,
                    created_by,
                ),
            )

            append_task_event(
                db,
                trace_id=trace_id,
                task_id=task_id,
                session_id=session_id,
                user_id=user_id,
                project_id=project_id,
                component="control_plane",
                stage="task",
                event="task.created",
                status_after=(
                    TaskStatus.QUEUED.value
                ),
                payload={
                    "action": action,
                    "specialist": specialist,
                    "priority": priority,
                },
            )

            db.execute("COMMIT;")

        except Exception as exc:

            db.execute("ROLLBACK;")

            raise TaskPersistenceError(
                "Falha ao criar tarefa."
            ) from exc

    return get_task(task_id)


# ============================================================
# TRANSIÇÃO DE ESTADO
# ============================================================

def transition_task(
    task_id: str,
    new_status: str,
    *,
    component: str = "control_plane",
    stage: str = "task",
    execution_verified: bool = False,
    requires_artifact: bool = False,
    artifact_verified: bool = False,
    error: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
    result_ref: str | None = None,
    evidence: dict[str, Any] | None = None,
    verification: (
        dict[str, Any] | None
    ) = None,
) -> dict[str, Any]:
    """
    Único caminho deste serviço para
    mudar o estado de uma tarefa.

    A autorização passa pela máquina
    determinística de estados.
    """

    initialize_database()

    with database_connection() as db:

        db.execute("BEGIN;")

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
                raise TaskNotFoundError(
                    f"Tarefa não encontrada: "
                    f"{task_id}"
                )

            current_status = row["status"]

            target = authorize_transition(
                current_status=current_status,
                new_status=new_status,
                requires_artifact=(
                    requires_artifact
                ),
                artifact_verified=(
                    artifact_verified
                ),
                execution_verified=(
                    execution_verified
                ),
            )

            now = utc_now()

            started_at = row["started_at"]
            finished_at = row["finished_at"]

            if (
                target == TaskStatus.RUNNING
                and started_at is None
            ):
                started_at = now

            if target in {
                TaskStatus.COMPLETED,
                TaskStatus.COMPLETED_WITH_WARNINGS,
                TaskStatus.FAILED,
                TaskStatus.CANCELED,
                TaskStatus.DEAD_LETTER,
            }:
                finished_at = now

            progress = row["progress"]

            if target in {
                TaskStatus.COMPLETED,
                TaskStatus.COMPLETED_WITH_WARNINGS,
            }:
                progress = 100

            db.execute(
                """
                UPDATE tasks
                SET
                    status = ?,
                    progress = ?,
                    updated_at = ?,
                    started_at = ?,
                    finished_at = ?,
                    error_json = ?,
                    result_json = ?,
                    result_ref = ?,
                    evidence_json = ?,
                    verification_json = ?
                WHERE task_id = ?;
                """,
                (
                    target.value,
                    progress,
                    now,
                    started_at,
                    finished_at,
                    (
                        json_dump(error)
                        if error is not None
                        else row["error_json"]
                    ),
                    (
                        json_dump(result)
                        if result is not None
                        else row["result_json"]
                    ),
                    (
                        result_ref
                        if result_ref is not None
                        else row["result_ref"]
                    ),
                    (
                        json_dump(evidence)
                        if evidence is not None
                        else row["evidence_json"]
                    ),
                    (
                        json_dump(verification)
                        if verification is not None
                        else row[
                            "verification_json"
                        ]
                    ),
                    task_id,
                ),
            )

            append_task_event(
                db,
                trace_id=row["trace_id"],
                task_id=task_id,
                session_id=row["session_id"],
                user_id=row["user_id"],
                project_id=row["project_id"],
                component=component,
                stage=stage,
                event="task.status_changed",
                status_before=current_status,
                status_after=target.value,
                payload={
                    "execution_verified": (
                        execution_verified
                    ),
                    "requires_artifact": (
                        requires_artifact
                    ),
                    "artifact_verified": (
                        artifact_verified
                    ),
                },
            )

            db.execute("COMMIT;")

        except Exception:
            db.execute("ROLLBACK;")
            raise

    return get_task(task_id)


# ============================================================
# PROGRESSO
# ============================================================

def update_progress(
    task_id: str,
    progress: float,
    *,
    component: str = "control_plane",
) -> dict[str, Any]:

    if progress < 0 or progress > 100:
        raise ValueError(
            "progress deve estar entre "
            "0 e 100."
        )

    initialize_database()

    with database_connection() as db:

        db.execute("BEGIN;")

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
                raise TaskNotFoundError(
                    f"Tarefa não encontrada: "
                    f"{task_id}"
                )

            if task_state.is_terminal(
                row["status"]
            ):
                raise TaskServiceError(
                    "Não é permitido alterar "
                    "progresso de tarefa terminal."
                )

            db.execute(
                """
                UPDATE tasks
                SET progress = ?,
                    updated_at = ?
                WHERE task_id = ?;
                """,
                (
                    progress,
                    utc_now(),
                    task_id,
                ),
            )

            append_task_event(
                db,
                trace_id=row["trace_id"],
                task_id=task_id,
                session_id=row["session_id"],
                user_id=row["user_id"],
                project_id=row["project_id"],
                component=component,
                stage="task",
                event="task.progress",
                payload={
                    "progress": progress,
                },
            )

            db.execute("COMMIT;")

        except Exception:
            db.execute("ROLLBACK;")
            raise

    return get_task(task_id)


# ============================================================
# CANCELAMENTO
# ============================================================

def request_cancel(
    task_id: str,
    *,
    requested_by: str = "user",
) -> dict[str, Any]:
    """
    Registra solicitação de cancelamento.

    Não mente dizendo que o worker já parou.
    """

    initialize_database()

    with database_connection() as db:

        db.execute("BEGIN;")

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
                raise TaskNotFoundError(
                    f"Tarefa não encontrada: "
                    f"{task_id}"
                )

            if task_state.is_terminal(
                row["status"]
            ):
                db.execute("COMMIT;")
                return task_row_to_dict(row)

            if bool(row["cancel_requested"]):
                db.execute("COMMIT;")
                return task_row_to_dict(row)

            now = utc_now()

            db.execute(
                """
                UPDATE tasks
                SET cancel_requested = 1,
                    updated_at = ?
                WHERE task_id = ?;
                """,
                (
                    now,
                    task_id,
                ),
            )

            append_task_event(
                db,
                trace_id=row["trace_id"],
                task_id=task_id,
                session_id=row["session_id"],
                user_id=row["user_id"],
                project_id=row["project_id"],
                component="control_plane",
                stage="cancel",
                event="task.cancel_requested",
                payload={
                    "requested_by": requested_by,
                },
            )

            db.execute("COMMIT;")

        except Exception:
            db.execute("ROLLBACK;")
            raise

    return get_task(task_id)


# ============================================================
# LISTAGEM BÁSICA
# ============================================================

def list_tasks(
    *,
    status: str | None = None,
    project_id: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:

    if limit < 1:
        limit = 1

    if limit > 500:
        limit = 500

    initialize_database()

    conditions: list[str] = []
    values: list[Any] = []

    if status is not None:

        normalized = (
            task_state.normalize_status(
                status
            )
        )

        conditions.append(
            "status = ?"
        )

        values.append(
            normalized.value
        )

    if project_id is not None:

        conditions.append(
            "project_id = ?"
        )

        values.append(
            project_id
        )

    where_clause = ""

    if conditions:
        where_clause = (
            "WHERE "
            + " AND ".join(conditions)
        )

    values.append(limit)

    query = f"""
        SELECT *
        FROM tasks
        {where_clause}
        ORDER BY
            priority ASC,
            created_at ASC
        LIMIT ?;
    """

    with database_connection() as db:

        rows = db.execute(
            query,
            tuple(values),
        ).fetchall()

    return [
        task_row_to_dict(row)
        for row in rows
    ]


# ============================================================
# SELF TEST
# ============================================================

def self_test() -> dict[str, bool]:
    """
    Teste local simples.

    Cria uma tarefa própria de teste
    sem chamar IA.
    """

    initialize_database()

    trace_id = new_id(
        "trace_test"
    )

    task = create_task(
        trace_id=trace_id,
        action="teste_task_service",
        specialist="analista_texto",
        inputs={
            "text": "teste isolado"
        },
        required_capabilities=[
            "text_generation"
        ],
    )

    task_id = task["task_id"]

    results: dict[str, bool] = {}

    results["created_queued"] = (
        task["status"]
        == TaskStatus.QUEUED.value
    )

    running = transition_task(
        task_id,
        TaskStatus.RUNNING.value,
    )

    results["running"] = (
        running["status"]
        == TaskStatus.RUNNING.value
    )

    fake_completion_blocked = False

    try:

        transition_task(
            task_id,
            TaskStatus.COMPLETED.value,
            execution_verified=False,
        )

    except TaskStateError:
        fake_completion_blocked = True

    results[
        "fake_completion_blocked"
    ] = fake_completion_blocked

    completed = transition_task(
        task_id,
        TaskStatus.COMPLETED.value,
        execution_verified=True,
    )

    results["completed_verified"] = (
        completed["status"]
        == TaskStatus.COMPLETED.value
    )

    events = list_task_events(
        task_id
    )

    results["events_created"] = (
        len(events) >= 3
    )

    results["all_passed"] = all(
        results.values()
    )

    return results


# ============================================================
# EXECUÇÃO MANUAL
# ============================================================

if __name__ == "__main__":

    print(
        "ChatCreova V23 Task Service"
    )

    results = self_test()

    for name, passed in results.items():

        print(
            f"{name}: "
            f"{'PASS' if passed else 'FAIL'}"
        )"""
ChatCreova AI
V23-FUNDACAO-01

Artifact Service

Responsabilidades:
- criar registros de artefatos;
- armazenar arquivos da V23;
- calcular SHA-256;
- verificar existência e tamanho;
- validar artefatos textuais;
- impedir READY sem verificação real;
- manter ligação artefato -> tarefa.

REGRA:
A declaração de uma IA não é prova de artefato.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import mimetypes
import os
import uuid

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ARTIFACT_ROOT = (
    BASE_DIR
    / "V23-data"
    / "artifacts"
)


# ============================================================
# CARREGAMENTO DE MÓDULO LOCAL
# ============================================================

def load_local_module(
    module_name: str,
    filename: str,
):
    path = BASE_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Módulo obrigatório não encontrado: "
            f"{path}"
        )

    spec = importlib.util.spec_from_file_location(
        module_name,
        path,
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Não foi possível carregar: "
            f"{filename}"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


database = load_local_module(
    "chatcreova_v23_database",
    "V23-database.py",
)

database_connection = (
    database.database_connection
)

initialize_database = (
    database.initialize_database
)


# ============================================================
# UTILITÁRIOS
# ============================================================

def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def new_id(prefix: str) -> str:
    return (
        f"{prefix}_"
        f"{uuid.uuid4().hex}"
    )


def json_dump(
    value: Any,
) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def json_load(
    value: str | None,
    default: Any,
) -> Any:

    if value is None:
        return default

    try:
        return json.loads(value)

    except (
        json.JSONDecodeError,
        TypeError,
    ):
        return default


# ============================================================
# EXCEÇÕES
# ============================================================

class ArtifactServiceError(Exception):
    """Erro-base de artefatos."""


class ArtifactNotFoundError(
    ArtifactServiceError
):
    """Artefato não encontrado."""


class ArtifactVerificationError(
    ArtifactServiceError
):
    """Artefato não passou na verificação."""


class UnsafeArtifactPathError(
    ArtifactServiceError
):
    """Tentativa de sair da pasta autorizada."""


# ============================================================
# DIRETÓRIOS
# ============================================================

def ensure_artifact_root() -> None:
    ARTIFACT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )


def artifact_directory(
    project_id: str | None,
    task_id: str,
) -> Path:

    ensure_artifact_root()

    project_segment = (
        project_id
        if project_id
        else "_no_project"
    )

    # IDs do sistema são esperados aqui.
    # Ainda assim removemos separadores de caminho.

    project_segment = (
        project_segment
        .replace("/", "_")
        .replace("\\", "_")
    )

    task_segment = (
        task_id
        .replace("/", "_")
        .replace("\\", "_")
    )

    directory = (
        ARTIFACT_ROOT
        / project_segment
        / task_segment
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


# ============================================================
# PROTEÇÃO DE CAMINHO
# ============================================================

def resolve_safe_path(
    path: Path,
) -> Path:

    root = ARTIFACT_ROOT.resolve()

    resolved = path.resolve()

    try:
        resolved.relative_to(root)

    except ValueError as exc:
        raise UnsafeArtifactPathError(
            "Caminho fora da área de "
            "artefatos da V23."
        ) from exc

    return resolved


# ============================================================
# HASH
# ============================================================

def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open("rb") as file:

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


# ============================================================
# MIME
# ============================================================

def detect_mime(
    path: Path,
) -> str:

    guessed, _ = mimetypes.guess_type(
        path.name
    )

    if guessed:
        return guessed

    return "application/octet-stream"


# ============================================================
# SERIALIZAÇÃO
# ============================================================

def artifact_row_to_dict(
    row,
) -> dict[str, Any]:

    return {
        "artifact_id": row["artifact_id"],
        "user_id": row["user_id"],
        "project_id": row["project_id"],
        "source_task_id": (
            row["source_task_id"]
        ),
        "producer": row["producer"],
        "type": row["type"],
        "mime": row["mime"],
        "version": row["version"],
        "storage_location": (
            row["storage_location"]
        ),
        "storage_backend": (
            row["storage_backend"]
        ),
        "size_bytes": row["size_bytes"],
        "hash": row["hash"],
        "hash_algorithm": (
            row["hash_algorithm"]
        ),
        "status": row["status"],
        "verify_status": (
            row["verify_status"]
        ),
        "verified_at": (
            row["verified_at"]
        ),
        "metadata": json_load(
            row["metadata_json"],
            {},
        ),
        "created_at": row["created_at"],
        "created_by": row["created_by"],
        "parent_artifacts": json_load(
            row["parent_artifacts_json"],
            [],
        ),
        "supersedes_artifact_id": (
            row[
                "supersedes_artifact_id"
            ]
        ),
        "visibility": row["visibility"],
        "access_scope": (
            row["access_scope"]
        ),
        "immutable": bool(
            row["immutable"]
        ),
        "expires_at": row["expires_at"],
        "retention": row["retention"],
        "usage": json_load(
            row["usage_json"],
            None,
        ),
        "preview_ref": row["preview_ref"],
    }


# ============================================================
# CONSULTA
# ============================================================

def get_artifact(
    artifact_id: str,
) -> dict[str, Any]:

    initialize_database()

    with database_connection() as db:

        row = db.execute(
            """
            SELECT *
            FROM artifacts
            WHERE artifact_id = ?;
            """,
            (artifact_id,),
        ).fetchone()

    if row is None:
        raise ArtifactNotFoundError(
            f"Artefato não encontrado: "
            f"{artifact_id}"
        )

    return artifact_row_to_dict(row)


# ============================================================
# VALIDAÇÃO DA TAREFA DE ORIGEM
# ============================================================

def get_source_task(
    task_id: str,
):

    initialize_database()

    with database_connection() as db:

        row = db.execute(
            """
            SELECT *
            FROM tasks
            WHERE task_id = ?;
            """,
            (task_id,),
        ).fetchone()

    if row is None:
        raise ArtifactServiceError(
            "A tarefa de origem não existe."
        )

    return row


# ============================================================
# CRIAÇÃO DO REGISTRO
# ============================================================

def create_artifact_record(
    *,
    source_task_id: str,
    producer: str,
    artifact_type: str,
    user_id: str | None = None,
    project_id: str | None = None,
    mime: str | None = None,
    storage_location: str | None = None,
    metadata: dict[str, Any] | None = None,
    parent_artifacts: list[str] | None = None,
    supersedes_artifact_id: (
        str | None
    ) = None,
    visibility: str = "private",
    access_scope: str | None = None,
    created_by: str = "control_plane",
) -> dict[str, Any]:

    source_task = get_source_task(
        source_task_id
    )

    if project_id is None:
        project_id = source_task[
            "project_id"
        ]

    if user_id is None:
        user_id = source_task[
            "user_id"
        ]

    artifact_id = new_id(
        "artifact"
    )

    now = utc_now()

    initialize_database()

    with database_connection() as db:

        db.execute(
            """
            INSERT INTO artifacts (
                artifact_id,
                user_id,
                project_id,
                source_task_id,
                producer,
                type,
                mime,
                version,
                storage_location,
                storage_backend,
                status,
                verify_status,
                metadata_json,
                created_at,
                created_by,
                parent_artifacts_json,
                supersedes_artifact_id,
                visibility,
                access_scope,
                immutable
            )
            VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?
            );
            """,
            (
                artifact_id,
                user_id,
                project_id,
                source_task_id,
                producer,
                artifact_type,
                mime,
                1,
                storage_location,
                "local",
                "PENDING",
                "NOT_VERIFIED",
                json_dump(
                    metadata or {}
                ),
                now,
                created_by,
                json_dump(
                    parent_artifacts or []
                ),
                supersedes_artifact_id,
                visibility,
                access_scope,
                1,
            ),
        )

    return get_artifact(
        artifact_id
    )


# ============================================================
# ARTEFATO TEXTUAL
# ============================================================

def create_text_artifact(
    *,
    source_task_id: str,
    text: str,
    producer: str,
    user_id: str | None = None,
    project_id: str | None = None,
    filename: str = "resultado.txt",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Materializa texto em arquivo físico.

    O arquivo ainda precisa passar
    pela verificação antes de READY.
    """

    if not isinstance(text, str):
        raise TypeError(
            "text deve ser string."
        )

    if not text.strip():
        raise ArtifactVerificationError(
            "Texto vazio não pode gerar "
            "artefato válido."
        )

    source_task = get_source_task(
        source_task_id
    )

    if project_id is None:
        project_id = source_task[
            "project_id"
        ]

    if user_id is None:
        user_id = source_task[
            "user_id"
        ]

    safe_filename = (
        Path(filename).name
    )

    if not safe_filename:
        safe_filename = (
            "resultado.txt"
        )

    directory = artifact_directory(
        project_id,
        source_task_id,
    )

    artifact_id = new_id(
        "artifact"
    )

    physical_name = (
        f"{artifact_id}-"
        f"{safe_filename}"
    )

    path = resolve_safe_path(
        directory / physical_name
    )

    # Escrita atômica simples:
    # primeiro temporário, depois replace.

    temp_path = resolve_safe_path(
        directory
        / f".{physical_name}.tmp"
    )

    try:

        with temp_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as file:

            file.write(text)

            file.flush()

            os.fsync(
                file.fileno()
            )

        os.replace(
            temp_path,
            path,
        )

    finally:

        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass

    now = utc_now()

    initialize_database()

    with database_connection() as db:

        db.execute(
            """
            INSERT INTO artifacts (
                artifact_id,
                user_id,
                project_id,
                source_task_id,
                producer,
                type,
                mime,
                version,
                storage_location,
                storage_backend,
                status,
                verify_status,
                metadata_json,
                created_at,
                created_by,
                parent_artifacts_json,
                visibility,
                immutable
            )
            VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            );
            """,
            (
                artifact_id,
                user_id,
                project_id,
                source_task_id,
                producer,
                "text",
                "text/plain",
                1,
                str(path),
                "local",
                "MATERIALIZING",
                "NOT_VERIFIED",
                json_dump(
                    metadata or {}
                ),
                now,
                "control_plane",
                "[]",
                "private",
                1,
            ),
        )

    return verify_artifact(
        artifact_id
    )


# ============================================================
# VERIFICAÇÃO
# ============================================================

def verify_artifact(
    artifact_id: str,
) -> dict[str, Any]:
    """
    Reabre o artefato fisicamente.

    Não confia no worker.

    READY só é gravado após PASS.
    """

    artifact = get_artifact(
        artifact_id
    )

    location = artifact[
        "storage_location"
    ]

    if not location:

        _mark_verification_failed(
            artifact_id,
            "MISSING_LOCATION",
        )

        raise ArtifactVerificationError(
            "Artefato não possui caminho "
            "físico."
        )

    path = resolve_safe_path(
        Path(location)
    )

    if not path.exists():

        _mark_verification_failed(
            artifact_id,
            "FILE_NOT_FOUND",
        )

        raise ArtifactVerificationError(
            "Arquivo físico não existe."
        )

    if not path.is_file():

        _mark_verification_failed(
            artifact_id,
            "NOT_A_FILE",
        )

        raise ArtifactVerificationError(
            "Local do artefato não é "
            "um arquivo."
        )

    size = path.stat().st_size

    if size <= 0:

        _mark_verification_failed(
            artifact_id,
            "EMPTY_FILE",
        )

        raise ArtifactVerificationError(
            "Arquivo vazio."
        )

    digest = sha256_file(
        path
    )

    mime = detect_mime(
        path
    )

    artifact_type = artifact[
        "type"
    ]

    if artifact_type == "text":

        try:

            content = path.read_text(
                encoding="utf-8"
            )

        except UnicodeDecodeError as exc:

            _mark_verification_failed(
                artifact_id,
                "INVALID_UTF8",
            )

            raise ArtifactVerificationError(
                "Artefato textual não é "
                "UTF-8 válido."
            ) from exc

        if not content.strip():

            _mark_verification_failed(
                artifact_id,
                "EMPTY_TEXT",
            )

            raise ArtifactVerificationError(
                "Artefato textual não possui "
                "conteúdo válido."
            )

        # Nosso artefato textual inicial
        # é text/plain.

        mime = "text/plain"

    now = utc_now()

    with database_connection() as db:

        db.execute(
            """
            UPDATE artifacts
            SET
                size_bytes = ?,
                hash = ?,
                hash_algorithm = ?,
                mime = ?,
                status = ?,
                verify_status = ?,
                verified_at = ?
            WHERE artifact_id = ?;
            """,
            (
                size,
                digest,
                "sha256",
                mime,
                "READY",
                "PASS",
                now,
                artifact_id,
            ),
        )

    return get_artifact(
        artifact_id
    )


# ============================================================
# MARCAÇÃO DE FALHA
# ============================================================

def _mark_verification_failed(
    artifact_id: str,
    reason: str,
) -> None:

    initialize_database()

    with database_connection() as db:

        row = db.execute(
            """
            SELECT metadata_json
            FROM artifacts
            WHERE artifact_id = ?;
            """,
            (artifact_id,),
        ).fetchone()

        if row is None:
            return

        metadata = json_load(
            row["metadata_json"],
            {},
        )

        metadata[
            "verification_failure"
        ] = {
            "reason": reason,
            "timestamp": utc_now(),
        }

        db.execute(
            """
            UPDATE artifacts
            SET
                status = ?,
                verify_status = ?,
                verified_at = ?,
                metadata_json = ?
            WHERE artifact_id = ?;
            """,
            (
                "CORRUPT",
                "FAIL",
                utc_now(),
                json_dump(metadata),
                artifact_id,
            ),
        )


# ============================================================
# CONSULTA DE VERIFICAÇÃO
# ============================================================

def is_artifact_verified(
    artifact_id: str,
) -> bool:

    artifact = get_artifact(
        artifact_id
    )

    return (
        artifact["status"] == "READY"
        and
        artifact["verify_status"] == "PASS"
        and
        bool(artifact["hash"])
        and
        bool(artifact["size_bytes"])
    )


# ============================================================
# LISTAGEM POR TAREFA
# ============================================================

def list_task_artifacts(
    task_id: str,
) -> list[dict[str, Any]]:

    initialize_database()

    with database_connection() as db:

        rows = db.execute(
            """
            SELECT *
            FROM artifacts
            WHERE source_task_id = ?
            ORDER BY created_at ASC;
            """,
            (task_id,),
        ).fetchall()

    return [
        artifact_row_to_dict(row)
        for row in rows
    ]


# ============================================================
# SELF TEST
# ============================================================

def self_test() -> dict[str, bool]:
    """
    Teste isolado do Artifact Service.

    Cria diretamente uma tarefa de teste
    mínima no banco apenas para satisfazer
    a FK do artefato.

    Não chama IA.
    """

    initialize_database()

    results: dict[str, bool] = {}

    task_id = new_id(
        "artifact_test_task"
    )

    trace_id = new_id(
        "artifact_test_trace"
    )

    now = utc_now()

    with database_connection() as db:

        db.execute(
            """
            INSERT INTO tasks (
                task_id,
                trace_id,
                specialist,
                action,
                status,
                created_at,
                updated_at,
                created_by
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?
            );
            """,
            (
                task_id,
                trace_id,
                "artifact_self_test",
                "artifact_self_test",
                "RUNNING",
                now,
                now,
                "self_test",
            ),
        )

    artifact = create_text_artifact(
        source_task_id=task_id,
        text=(
            "ChatCreova V23 "
            "artifact verification test."
        ),
        producer="artifact_self_test",
        filename="teste.txt",
    )

    results[
        "artifact_created"
    ] = bool(
        artifact["artifact_id"]
    )

    results[
        "artifact_ready"
    ] = (
        artifact["status"]
        == "READY"
    )

    results[
        "verification_pass"
    ] = (
        artifact["verify_status"]
        == "PASS"
    )

    results[
        "size_valid"
    ] = (
        artifact["size_bytes"] > 0
    )

    results[
        "hash_valid"
    ] = (
        isinstance(
            artifact["hash"],
            str,
        )
        and
        len(artifact["hash"]) == 64
    )

    results[
        "physical_file_exists"
    ] = Path(
        artifact["storage_location"]
    ).exists()

    results[
        "verified_query"
    ] = is_artifact_verified(
        artifact["artifact_id"]
    )

    results[
        "all_passed"
    ] = all(
        results.values()
    )

    return results


# ============================================================
# EXECUÇÃO MANUAL
# ============================================================

if __name__ == "__main__":

    print(
        "ChatCreova V23 "
        "Artifact Service"
    )

    test_results = self_test()

    for name, passed in (
        test_results.items()
    ):

        print(
            f"{name}: "
            f"{'PASS' if passed else 'FAIL'}"
        )
