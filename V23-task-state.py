"""
ChatCreova AI
V23-FUNDACAO-01

Arquivo principal do Control Plane.

REGRA:
- V22 permanece congelada.
- V23 é laboratório.
- IA não declara tarefa concluída.
- Estado oficial pertence ao Control Plane.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


# ============================================================
# IDENTIDADE DA VERSÃO
# ============================================================

APP_NAME = "ChatCreova AI Control Plane"
APP_VERSION = "V23-FUNDACAO-01"
APP_STATUS = "LABORATORIO"


# ============================================================
# FUNÇÕES BÁSICAS
# ============================================================

def utc_now() -> str:
    """Retorna horário UTC padronizado."""
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    """Cria IDs independentes de banco/rowid."""
    return f"{prefix}_{uuid.uuid4().hex}"


def new_trace_id() -> str:
    return new_id("trace")


# ============================================================
# CONTRATOS INICIAIS
# ============================================================

class HealthResponse(BaseModel):
    ok: bool
    app: str
    version: str
    status: str
    timestamp: str


class TaskCreate(BaseModel):
    """
    Contrato mínimo para criação de tarefa.

    Será ampliado nos próximos módulos da fundação.
    """

    action: str = Field(
        min_length=1,
        max_length=120,
        description="Ação solicitada",
    )

    project_id: str | None = None
    session_id: str | None = None

    specialist: str = Field(
        default="analista_texto",
        max_length=120,
    )

    inputs: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)

    priority: int = Field(
        default=100,
        ge=0,
        le=1000,
    )


class TaskCreated(BaseModel):
    task_id: str
    trace_id: str
    status: str
    action: str
    specialist: str
    created_at: str


# ============================================================
# APLICAÇÃO FASTAPI
# ============================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Fundação experimental da ChatCreova AI V23. "
        "V22 permanece congelada e independente."
    ),
)


# ============================================================
# CORS DE DESENVOLVIMENTO
# ============================================================

# IMPORTANTE:
# Esta lista é explícita de propósito.
# Não usar "*" junto com credenciais.
#
# Podemos ajustar depois quando confirmarmos exatamente
# de onde o frontend V23 será servido.

DEV_ORIGINS = [
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Trace-ID"],
)


# ============================================================
# MIDDLEWARE DE TRACE
# ============================================================

@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    """
    Todo request recebe trace_id.

    Se futuramente um cliente autorizado enviar um trace
    existente, poderemos implementar correlação controlada.
    Por enquanto cada request cria seu próprio trace.
    """

    trace_id = new_trace_id()
    request.state.trace_id = trace_id

    started = time.perf_counter()

    try:
        response = await call_next(request)

    except Exception:
        # Não expor detalhes internos ao frontend.
        response = JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Erro interno no Control Plane.",
                    "retryable": False,
                    "stage": "api",
                    "trace_id": trace_id,
                },
            },
        )

    elapsed_ms = round(
        (time.perf_counter() - started) * 1000,
        2,
    )

    response.headers["X-Trace-ID"] = trace_id
    response.headers["X-Process-Time-MS"] = str(elapsed_ms)

    return response


# ============================================================
# ROTAS BÁSICAS
# ============================================================

@app.get("/")
async def root(request: Request):
    """
    Identificação básica do Control Plane.
    """

    return {
        "ok": True,
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": APP_STATUS,
        "trace_id": request.state.trace_id,
        "message": "ChatCreova V23 Control Plane ativo.",
    }


@app.get(
    "/health",
    response_model=HealthResponse,
)
async def health():
    """
    Health check básico.

    Nesta primeira etapa verifica apenas se a API está viva.
    Ollama, banco e workers ganharão health checks próprios.
    """

    return HealthResponse(
        ok=True,
        app=APP_NAME,
        version=APP_VERSION,
        status=APP_STATUS,
        timestamp=utc_now(),
    )


@app.get("/version")
async def version(request: Request):
    """
    Permite confirmar que estamos executando V23,
    evitando confusão com V22.
    """

    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": APP_STATUS,
        "trace_id": request.state.trace_id,
        "v22_policy": "FROZEN_DO_NOT_MODIFY",
    }


# ============================================================
# PRIMEIRA ENTRADA DE TAREFA
# ============================================================

@app.post(
    "/api/v23/tasks",
    response_model=TaskCreated,
    status_code=201,
)
async def create_task(
    payload: TaskCreate,
    request: Request,
):
    """
    Primeira prova do contrato de tarefa.

    IMPORTANTE:
    Ainda NÃO executa Qwen.
    Ainda NÃO chama especialista.
    Ainda NÃO grava SQLite.

    Nesta etapa estamos provando:
    - API;
    - validação;
    - task_id;
    - trace_id;
    - contrato básico.

    Persistência e máquina de estados entram
    nos próximos arquivos.
    """

    task_id = new_id("task")
    trace_id = request.state.trace_id
    created_at = utc_now()

    return TaskCreated(
        task_id=task_id,
        trace_id=trace_id,
        status="QUEUED",
        action=payload.action,
        specialist=payload.specialist,
        created_at=created_at,
    )


# ============================================================
# ERRO 404 PADRONIZADO
# ============================================================

@app.exception_handler(404)
async def not_found_handler(
    request: Request,
    exc,
):
    trace_id = getattr(
        request.state,
        "trace_id",
        new_trace_id(),
    )

    return JSONResponse(
        status_code=404,
        content={
            "ok": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "Rota não encontrada.",
                "retryable": False,
                "stage": "api",
                "trace_id": trace_id,
            },
        },
    )


# ============================================================
# INICIALIZAÇÃO LOCAL
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "V23-main:app",
        host="127.0.0.1",
        port=8230,
        reload=False,
    )"""
ChatCreova AI
V23-FUNDACAO-01

Módulo de banco de dados.

Responsabilidades:
- SQLite local
- WAL
- criação das tabelas iniciais
- conexão centralizada
- base para tasks, events, artifacts, memory e sessions

REGRA:
Este módulo NÃO executa IA.
Este módulo NÃO decide tarefas.
Este módulo NÃO modifica V22.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "V23-data"

DATABASE_PATH = DATA_DIR / "chatcreova-v23.db"


# ============================================================
# DIRETÓRIO DE DADOS
# ============================================================

def ensure_data_directory() -> None:
    """
    Garante que a pasta de dados da V23 exista.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# CONEXÃO
# ============================================================

def connect() -> sqlite3.Connection:
    """
    Abre uma conexão SQLite configurada para a V23.

    Cada chamada recebe sua própria conexão.
    """

    ensure_data_directory()

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30,
        isolation_level=None,
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA journal_mode=WAL;"
    )

    connection.execute(
        "PRAGMA foreign_keys=ON;"
    )

    connection.execute(
        "PRAGMA busy_timeout=30000;"
    )

    return connection


# ============================================================
# CONTEXT MANAGER
# ============================================================

@contextmanager
def database_connection() -> Generator[
    sqlite3.Connection,
    None,
    None,
]:
    """
    Uso:

    with database_connection() as db:
        ...

    Fecha a conexão automaticamente.
    """

    db = connect()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# SCHEMA — SESSIONS
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

    metadata_json TEXT
        NOT NULL
        DEFAULT '{}'
);
"""


# ============================================================
# SCHEMA — TASKS
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

    inputs_json TEXT
        NOT NULL
        DEFAULT '{}',

    constraints_json TEXT
        NOT NULL
        DEFAULT '{}',

    priority INTEGER
        NOT NULL
        DEFAULT 100,

    status TEXT
        NOT NULL
        DEFAULT 'QUEUED',

    progress REAL
        NOT NULL
        DEFAULT 0,

    attempt INTEGER
        NOT NULL
        DEFAULT 0,

    max_attempts INTEGER
        NOT NULL
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

    cancel_requested INTEGER
        NOT NULL
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

    schema_version INTEGER
        NOT NULL
        DEFAULT 1,

    created_by TEXT
        NOT NULL
        DEFAULT 'control_plane',

    FOREIGN KEY (session_id)
        REFERENCES sessions(session_id),

    FOREIGN KEY (parent_task_id)
        REFERENCES tasks(task_id)
);
"""


# ============================================================
# SCHEMA — TASK EVENTS
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

    payload_json TEXT
        NOT NULL
        DEFAULT '{}',

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id)
);
"""


# ============================================================
# SCHEMA — ARTIFACTS
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

    version INTEGER
        NOT NULL
        DEFAULT 1,

    storage_location TEXT,

    storage_backend TEXT
        NOT NULL
        DEFAULT 'local',

    size_bytes INTEGER,

    hash TEXT,

    hash_algorithm TEXT
        DEFAULT 'sha256',

    status TEXT
        NOT NULL
        DEFAULT 'PENDING',

    verify_status TEXT
        NOT NULL
        DEFAULT 'NOT_VERIFIED',

    verified_at TEXT,

    metadata_json TEXT
        NOT NULL
        DEFAULT '{}',

    created_at TEXT NOT NULL,

    created_by TEXT
        NOT NULL
        DEFAULT 'control_plane',

    parent_artifacts_json TEXT
        NOT NULL
        DEFAULT '[]',

    supersedes_artifact_id TEXT,

    visibility TEXT
        NOT NULL
        DEFAULT 'private',

    access_scope TEXT,

    immutable INTEGER
        NOT NULL
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
# SCHEMA — MEMORY RECORDS
# ============================================================

CREATE_MEMORY_RECORDS_TABLE = """
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

    provenance_json TEXT
        NOT NULL
        DEFAULT '{}',

    promoted_by TEXT NOT NULL,

    created_at TEXT NOT NULL,

    updated_at TEXT NOT NULL,

    active INTEGER
        NOT NULL
        DEFAULT 1
);
"""


# ============================================================
# SCHEMA — USAGE EVENTS
# ============================================================

CREATE_USAGE_EVENTS_TABLE = """
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

    metadata_json TEXT
        NOT NULL
        DEFAULT '{}',

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id)
);
"""


# ============================================================
# ÍNDICES
# ============================================================

CREATE_INDEXES = (
    """
    CREATE INDEX IF NOT EXISTS
    idx_tasks_status_priority
    ON tasks(status, priority, created_at);
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
    ON task_events(task_id, timestamp);
    """,

    """
    CREATE INDEX IF NOT EXISTS
    idx_events_trace
    ON task_events(trace_id, timestamp);
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
    ON usage_events(task_id, timestamp);
    """,
)


# ============================================================
# INICIALIZAÇÃO
# ============================================================

def initialize_database() -> None:
    """
    Cria a fundação do banco V23.

    Esta função é idempotente:
    pode ser chamada novamente sem apagar os dados existentes.
    """

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
                CREATE_MEMORY_RECORDS_TABLE
            )

            db.execute(
                CREATE_USAGE_EVENTS_TABLE
            )

            for statement in CREATE_INDEXES:
                db.execute(statement)

            db.execute("COMMIT;")

        except Exception:
            db.execute("ROLLBACK;")
            raise


# ============================================================
# HEALTH CHECK DO BANCO
# ============================================================

def database_health() -> dict:
    """
    Verifica se o SQLite responde.

    Não altera dados.
    """

    try:
        with database_connection() as db:

            row = db.execute(
                "SELECT sqlite_version() AS version;"
            ).fetchone()

            journal = db.execute(
                "PRAGMA journal_mode;"
            ).fetchone()

        return {
            "ok": True,
            "database": "sqlite",
            "sqlite_version": row["version"],
            "journal_mode": journal[0],
            "path": str(DATABASE_PATH),
        }

    except Exception as exc:

        return {
            "ok": False,
            "database": "sqlite",
            "error": type(exc).__name__,
        }


# ============================================================
# TESTE MANUAL ISOLADO
# ============================================================

if __name__ == "__main__":

    initialize_database()

    health = database_health()

    print(
        "ChatCreova V23 Database"
    )

    print(
        health
    )"""
ChatCreova AI
V23-FUNDACAO-01

Módulo de estados de tarefas.

Responsabilidades:
- definir estados oficiais;
- controlar transições permitidas;
- impedir transições inválidas;
- separar decisão determinística de resposta da IA;
- preparar gate de evidência.

REGRA:
Nenhuma IA altera diretamente o estado oficial.
"""

from __future__ import annotations

from enum import Enum
from typing import Final


# ============================================================
# ESTADOS OFICIAIS
# ============================================================

class TaskStatus(str, Enum):

    QUEUED = "QUEUED"

    RUNNING = "RUNNING"

    WAITING_INPUT = "WAITING_INPUT"

    WAITING_DEPENDENCY = "WAITING_DEPENDENCY"

    WAITING_CAPABILITY = "WAITING_CAPABILITY"

    COMPLETED = "COMPLETED"

    COMPLETED_WITH_WARNINGS = (
        "COMPLETED_WITH_WARNINGS"
    )

    FAILED = "FAILED"

    CANCELED = "CANCELED"

    DEAD_LETTER = "DEAD_LETTER"


# ============================================================
# ESTADOS TERMINAIS
# ============================================================

TERMINAL_STATES: Final[
    frozenset[TaskStatus]
] = frozenset(
    {
        TaskStatus.COMPLETED,
        TaskStatus.COMPLETED_WITH_WARNINGS,
        TaskStatus.FAILED,
        TaskStatus.CANCELED,
        TaskStatus.DEAD_LETTER,
    }
)


# ============================================================
# TRANSIÇÕES PERMITIDAS
# ============================================================

ALLOWED_TRANSITIONS: Final[
    dict[TaskStatus, frozenset[TaskStatus]]
] = {

    TaskStatus.QUEUED: frozenset(
        {
            TaskStatus.RUNNING,
            TaskStatus.WAITING_INPUT,
            TaskStatus.WAITING_DEPENDENCY,
            TaskStatus.WAITING_CAPABILITY,
            TaskStatus.CANCELED,
            TaskStatus.FAILED,
        }
    ),

    TaskStatus.RUNNING: frozenset(
        {
            TaskStatus.QUEUED,
            TaskStatus.WAITING_INPUT,
            TaskStatus.WAITING_DEPENDENCY,
            TaskStatus.WAITING_CAPABILITY,
            TaskStatus.COMPLETED,
            TaskStatus.COMPLETED_WITH_WARNINGS,
            TaskStatus.FAILED,
            TaskStatus.CANCELED,
            TaskStatus.DEAD_LETTER,
        }
    ),

    TaskStatus.WAITING_INPUT: frozenset(
        {
            TaskStatus.QUEUED,
            TaskStatus.RUNNING,
            TaskStatus.CANCELED,
            TaskStatus.FAILED,
        }
    ),

    TaskStatus.WAITING_DEPENDENCY: frozenset(
        {
            TaskStatus.QUEUED,
            TaskStatus.RUNNING,
            TaskStatus.CANCELED,
            TaskStatus.FAILED,
            TaskStatus.DEAD_LETTER,
        }
    ),

    TaskStatus.WAITING_CAPABILITY: frozenset(
        {
            TaskStatus.QUEUED,
            TaskStatus.RUNNING,
            TaskStatus.CANCELED,
            TaskStatus.FAILED,
            TaskStatus.DEAD_LETTER,
        }
    ),

    TaskStatus.COMPLETED: frozenset(),

    TaskStatus.COMPLETED_WITH_WARNINGS: (
        frozenset()
    ),

    TaskStatus.FAILED: frozenset(
        {
            TaskStatus.QUEUED,
            TaskStatus.DEAD_LETTER,
        }
    ),

    TaskStatus.CANCELED: frozenset(),

    TaskStatus.DEAD_LETTER: frozenset(),
}


# ============================================================
# EXCEÇÕES
# ============================================================

class TaskStateError(Exception):
    """Erro-base da máquina de estados."""


class UnknownTaskStatusError(TaskStateError):
    """Estado desconhecido."""


class InvalidTaskTransitionError(TaskStateError):
    """Transição não autorizada."""


class EvidenceRequiredError(TaskStateError):
    """
    Tentativa de concluir tarefa sem
    evidência/verificação suficiente.
    """


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalize_status(
    status: str | TaskStatus,
) -> TaskStatus:

    if isinstance(status, TaskStatus):
        return status

    try:
        return TaskStatus(status)

    except ValueError as exc:

        raise UnknownTaskStatusError(
            f"Estado de tarefa desconhecido: {status}"
        ) from exc


# ============================================================
# CONSULTAS
# ============================================================

def is_terminal(
    status: str | TaskStatus,
) -> bool:

    normalized = normalize_status(status)

    return normalized in TERMINAL_STATES


def can_transition(
    current_status: str | TaskStatus,
    new_status: str | TaskStatus,
) -> bool:

    current = normalize_status(
        current_status
    )

    target = normalize_status(
        new_status
    )

    return target in ALLOWED_TRANSITIONS[current]


# ============================================================
# VALIDAÇÃO DA TRANSIÇÃO
# ============================================================

def validate_transition(
    current_status: str | TaskStatus,
    new_status: str | TaskStatus,
) -> None:

    current = normalize_status(
        current_status
    )

    target = normalize_status(
        new_status
    )

    if current == target:

        raise InvalidTaskTransitionError(
            "Transição para o mesmo estado "
            f"não é permitida: {current.value}"
        )

    if current in TERMINAL_STATES:

        # FAILED possui exceção controlada
        # para retry/dead-letter.
        if (
            current == TaskStatus.FAILED
            and target
            in ALLOWED_TRANSITIONS[current]
        ):
            return

        raise InvalidTaskTransitionError(
            "Estado terminal não permite "
            f"esta transição: "
            f"{current.value} -> {target.value}"
        )

    if target not in ALLOWED_TRANSITIONS[current]:

        raise InvalidTaskTransitionError(
            "Transição não permitida: "
            f"{current.value} -> {target.value}"
        )


# ============================================================
# GATE DE CONCLUSÃO
# ============================================================

def validate_completion_gate(
    *,
    target_status: str | TaskStatus,
    requires_artifact: bool,
    artifact_verified: bool,
    execution_verified: bool,
) -> None:
    """
    Impede conclusão baseada apenas
    em texto produzido por IA.

    Para COMPLETED:
    - execução deve estar verificada;
    - se a tarefa exige artefato,
      o artefato também deve estar verificado.
    """

    target = normalize_status(
        target_status
    )

    completion_states = {
        TaskStatus.COMPLETED,
        TaskStatus.COMPLETED_WITH_WARNINGS,
    }

    if target not in completion_states:
        return

    if not execution_verified:

        raise EvidenceRequiredError(
            "A tarefa não pode ser concluída: "
            "execução ainda não foi verificada."
        )

    if (
        requires_artifact
        and not artifact_verified
    ):

        raise EvidenceRequiredError(
            "A tarefa não pode ser concluída: "
            "artefato obrigatório não foi "
            "verificado."
        )


# ============================================================
# VALIDAÇÃO COMPLETA
# ============================================================

def authorize_transition(
    *,
    current_status: str | TaskStatus,
    new_status: str | TaskStatus,
    requires_artifact: bool = False,
    artifact_verified: bool = False,
    execution_verified: bool = False,
) -> TaskStatus:
    """
    Ponto determinístico de autorização.

    Não altera banco.
    Não executa IA.
    Não confia em texto do modelo.

    Apenas valida se a transição pode
    acontecer.
    """

    current = normalize_status(
        current_status
    )

    target = normalize_status(
        new_status
    )

    validate_transition(
        current,
        target,
    )

    validate_completion_gate(
        target_status=target,
        requires_artifact=requires_artifact,
        artifact_verified=artifact_verified,
        execution_verified=execution_verified,
    )

    return target


# ============================================================
# TESTES INTERNOS SIMPLES
# ============================================================

def self_test() -> dict:
    """
    Pequeno teste isolado da máquina
    de estados.

    Não acessa banco.
    """

    results: dict[str, bool] = {}

    # QUEUED -> RUNNING deve funcionar.

    try:

        authorize_transition(
            current_status="QUEUED",
            new_status="RUNNING",
        )

        results[
            "queued_to_running"
        ] = True

    except TaskStateError:

        results[
            "queued_to_running"
        ] = False

    # QUEUED -> COMPLETED deve falhar.

    try:

        authorize_transition(
            current_status="QUEUED",
            new_status="COMPLETED",
            execution_verified=True,
        )

        results[
            "queued_to_completed_blocked"
        ] = False

    except TaskStateError:

        results[
            "queued_to_completed_blocked"
        ] = True

    # RUNNING -> COMPLETED sem evidência
    # deve falhar.

    try:

        authorize_transition(
            current_status="RUNNING",
            new_status="COMPLETED",
            requires_artifact=False,
            execution_verified=False,
        )

        results[
            "fake_completion_blocked"
        ] = False

    except EvidenceRequiredError:

        results[
            "fake_completion_blocked"
        ] = True

    # RUNNING -> COMPLETED com execução
    # verificada deve funcionar quando
    # não exige artefato.

    try:

        authorize_transition(
            current_status="RUNNING",
            new_status="COMPLETED",
            requires_artifact=False,
            execution_verified=True,
        )

        results[
            "verified_completion"
        ] = True

    except TaskStateError:

        results[
            "verified_completion"
        ] = False

    # Se exige artefato, execução sozinha
    # não basta.

    try:

        authorize_transition(
            current_status="RUNNING",
            new_status="COMPLETED",
            requires_artifact=True,
            artifact_verified=False,
            execution_verified=True,
        )

        results[
            "missing_artifact_blocked"
        ] = False

    except EvidenceRequiredError:

        results[
            "missing_artifact_blocked"
        ] = True

    # Execução + artefato verificados.

    try:

        authorize_transition(
            current_status="RUNNING",
            new_status="COMPLETED",
            requires_artifact=True,
            artifact_verified=True,
            execution_verified=True,
        )

        results[
            "verified_artifact_completion"
        ] = True

    except TaskStateError:

        results[
            "verified_artifact_completion"
        ] = False

    results["all_passed"] = all(
        results.values()
    )

    return results


# ============================================================
# EXECUÇÃO MANUAL
# ============================================================

if __name__ == "__main__":

    test_results = self_test()

    print(
        "ChatCreova V23 Task State"
    )

    for name, passed in test_results.items():

        print(
            f"{name}: "
            f"{'PASS' if passed else 'FAIL'}"
        )
