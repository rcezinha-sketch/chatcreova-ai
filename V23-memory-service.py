"""
ChatCreova AI
V23-FUNDACAO-01

Memory Service

Responsabilidades:
- memória estruturada;
- cinco escopos de memória;
- procedência;
- promoção controlada;
- entidade ativa;
- continuidade de projeto/campanha;
- resolução determinística de referências.

REGRA:
Contexto não é memória.
A IA não grava memória permanente silenciosamente.
"""

from __future__ import annotations

import importlib.util
import json
import uuid

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

VALID_SCOPES = {
    "session",
    "user",
    "project",
    "specialist",
    "task",
}

ACTIVE_ENTITY_KEY = "active_entity"


# ============================================================
# CARREGAMENTO DO BANCO
# ============================================================

def load_local_module(
    module_name: str,
    filename: str,
):
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

database_connection = database.database_connection
initialize_database = database.initialize_database


# ============================================================
# UTILITÁRIOS
# ============================================================

def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def json_dump(value: Any) -> str:
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

class MemoryServiceError(Exception):
    """Erro-base do serviço de memória."""


class InvalidMemoryScopeError(
    MemoryServiceError
):
    """Escopo de memória inválido."""


class MemoryNotFoundError(
    MemoryServiceError
):
    """Memória não encontrada."""


class MemoryPromotionError(
    MemoryServiceError
):
    """Promoção de memória não autorizada."""


class AmbiguousReferenceError(
    MemoryServiceError
):
    """
    Mais de uma entidade pode corresponder
    à referência solicitada.
    """


# ============================================================
# VALIDAÇÃO
# ============================================================

def validate_scope(scope: str) -> str:

    normalized = scope.strip().lower()

    if normalized not in VALID_SCOPES:
        raise InvalidMemoryScopeError(
            f"Escopo inválido: {scope}"
        )

    return normalized


def validate_promotion(
    *,
    promoted_by: str,
    provenance: dict[str, Any],
) -> None:
    """
    Toda memória persistente deve dizer
    quem promoveu e de onde veio.
    """

    if not promoted_by.strip():
        raise MemoryPromotionError(
            "promoted_by é obrigatório."
        )

    if not provenance:
        raise MemoryPromotionError(
            "provenance é obrigatória."
        )

    allowed_promoters = {
        "user",
        "control_plane",
        "deterministic_extractor",
        "system_import",
    }

    if promoted_by not in allowed_promoters:
        raise MemoryPromotionError(
            "Componente não autorizado a "
            "promover memória permanente."
        )


# ============================================================
# SERIALIZAÇÃO
# ============================================================

def memory_row_to_dict(
    row,
) -> dict[str, Any]:

    return {
        "memory_id": row["memory_id"],
        "scope": row["scope"],
        "user_id": row["user_id"],
        "project_id": row["project_id"],
        "session_id": row["session_id"],
        "specialist": row["specialist"],
        "task_id": row["task_id"],
        "memory_type": row["memory_type"],
        "key": row["key"],
        "value": json_load(
            row["value_json"],
            None,
        ),
        "provenance": json_load(
            row["provenance_json"],
            {},
        ),
        "promoted_by": row["promoted_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "active": bool(row["active"]),
    }


# ============================================================
# GRAVAÇÃO CONTROLADA
# ============================================================

def create_memory(
    *,
    scope: str,
    memory_type: str,
    value: Any,
    provenance: dict[str, Any],
    promoted_by: str,
    key: str | None = None,
    user_id: str | None = None,
    project_id: str | None = None,
    session_id: str | None = None,
    specialist: str | None = None,
    task_id: str | None = None,
) -> dict[str, Any]:

    scope = validate_scope(scope)

    validate_promotion(
        promoted_by=promoted_by,
        provenance=provenance,
    )

    if not memory_type.strip():
        raise ValueError(
            "memory_type é obrigatório."
        )

    initialize_database()

    memory_id = new_id("memory")
    now = utc_now()

    with database_connection() as db:

        db.execute(
            """
            INSERT INTO memory_records (
                memory_id,
                scope,
                user_id,
                project_id,
                session_id,
                specialist,
                task_id,
                memory_type,
                key,
                value_json,
                provenance_json,
                promoted_by,
                created_at,
                updated_at,
                active
            )
            VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?
            );
            """,
            (
                memory_id,
                scope,
                user_id,
                project_id,
                session_id,
                specialist,
                task_id,
                memory_type,
                key,
                json_dump(value),
                json_dump(provenance),
                promoted_by,
                now,
                now,
                1,
            ),
        )

    return get_memory(memory_id)


# ============================================================
# CONSULTA POR ID
# ============================================================

def get_memory(
    memory_id: str,
) -> dict[str, Any]:

    initialize_database()

    with database_connection() as db:

        row = db.execute(
            """
            SELECT *
            FROM memory_records
            WHERE memory_id = ?;
            """,
            (memory_id,),
        ).fetchone()

    if row is None:
        raise MemoryNotFoundError(
            f"Memória não encontrada: {memory_id}"
        )

    return memory_row_to_dict(row)


# ============================================================
# DESATIVAÇÃO
# ============================================================

def deactivate_memory(
    memory_id: str,
) -> dict[str, Any]:

    initialize_database()

    existing = get_memory(memory_id)

    if not existing["active"]:
        return existing

    with database_connection() as db:

        db.execute(
            """
            UPDATE memory_records
            SET
                active = 0,
                updated_at = ?
            WHERE memory_id = ?;
            """,
            (
                utc_now(),
                memory_id,
            ),
        )

    return get_memory(memory_id)


# ============================================================
# BUSCA
# ============================================================

def search_memory(
    *,
    scope: str | None = None,
    user_id: str | None = None,
    project_id: str | None = None,
    session_id: str | None = None,
    specialist: str | None = None,
    task_id: str | None = None,
    memory_type: str | None = None,
    key: str | None = None,
    active_only: bool = True,
    limit: int = 100,
) -> list[dict[str, Any]]:

    initialize_database()

    conditions: list[str] = []
    values: list[Any] = []

    if scope is not None:
        conditions.append("scope = ?")
        values.append(
            validate_scope(scope)
        )

    if user_id is not None:
        conditions.append("user_id = ?")
        values.append(user_id)

    if project_id is not None:
        conditions.append("project_id = ?")
        values.append(project_id)

    if session_id is not None:
        conditions.append("session_id = ?")
        values.append(session_id)

    if specialist is not None:
        conditions.append("specialist = ?")
        values.append(specialist)

    if task_id is not None:
        conditions.append("task_id = ?")
        values.append(task_id)

    if memory_type is not None:
        conditions.append(
            "memory_type = ?"
        )
        values.append(memory_type)

    if key is not None:
        conditions.append("key = ?")
        values.append(key)

    if active_only:
        conditions.append("active = 1")

    if limit < 1:
        limit = 1

    if limit > 500:
        limit = 500

    where_clause = ""

    if conditions:
        where_clause = (
            "WHERE "
            + " AND ".join(conditions)
        )

    values.append(limit)

    query = f"""
        SELECT *
        FROM memory_records
        {where_clause}
        ORDER BY updated_at DESC
        LIMIT ?;
    """

    with database_connection() as db:

        rows = db.execute(
            query,
            tuple(values),
        ).fetchall()

    return [
        memory_row_to_dict(row)
        for row in rows
    ]


# ============================================================
# ENTIDADE ATIVA
# ============================================================

def set_active_entity(
    *,
    entity_type: str,
    entity_id: str,
    entity_name: str,
    user_id: str | None,
    project_id: str | None,
    session_id: str | None = None,
    last_task_id: str | None = None,
    last_artifact_id: str | None = None,
    extra: dict[str, Any] | None = None,
    promoted_by: str = "control_plane",
) -> dict[str, Any]:
    """
    Mantém uma referência estruturada
    para coisas como:

    campanha ativa,
    documento ativo,
    projeto ativo.
    """

    if not entity_type.strip():
        raise ValueError(
            "entity_type é obrigatório."
        )

    if not entity_id.strip():
        raise ValueError(
            "entity_id é obrigatório."
        )

    # Desativa a entidade ativa anterior
    # do mesmo tipo no mesmo contexto.

    previous = search_memory(
        scope="project",
        user_id=user_id,
        project_id=project_id,
        memory_type="active_entity",
        key=entity_type,
        active_only=True,
        limit=100,
    )

    for memory in previous:
        deactivate_memory(
            memory["memory_id"]
        )

    value = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_name": entity_name,
        "last_task_id": last_task_id,
        "last_artifact_id": (
            last_artifact_id
        ),
        "extra": extra or {},
    }

    return create_memory(
        scope="project",
        memory_type="active_entity",
        key=entity_type,
        value=value,
        provenance={
            "source": "control_plane",
            "reason": "active_entity_update",
        },
        promoted_by=promoted_by,
        user_id=user_id,
        project_id=project_id,
        session_id=session_id,
        task_id=last_task_id,
    )


# ============================================================
# OBTÉM ENTIDADE ATIVA
# ============================================================

def get_active_entity(
    *,
    entity_type: str,
    user_id: str | None,
    project_id: str | None,
) -> dict[str, Any] | None:

    memories = search_memory(
        scope="project",
        user_id=user_id,
        project_id=project_id,
        memory_type="active_entity",
        key=entity_type,
        active_only=True,
        limit=10,
    )

    if not memories:
        return None

    if len(memories) > 1:
        raise AmbiguousReferenceError(
            "Mais de uma entidade ativa "
            "foi encontrada."
        )

    return memories[0]


# ============================================================
# REGISTRO DE ENTIDADE
# ============================================================

def register_entity(
    *,
    entity_type: str,
    entity_id: str,
    entity_name: str,
    user_id: str | None,
    project_id: str | None,
    session_id: str | None = None,
    task_id: str | None = None,
    artifact_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    promoted_by: str = "control_plane",
) -> dict[str, Any]:

    value = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_name": entity_name,
        "task_id": task_id,
        "artifact_id": artifact_id,
        "metadata": metadata or {},
    }

    return create_memory(
        scope="project",
        memory_type="entity",
        key=entity_type,
        value=value,
        provenance={
            "source": "control_plane",
            "reason": "entity_registered",
        },
        promoted_by=promoted_by,
        user_id=user_id,
        project_id=project_id,
        session_id=session_id,
        task_id=task_id,
    )


# ============================================================
# RESOLUÇÃO DE REFERÊNCIA
# ============================================================

def resolve_entity_reference(
    *,
    entity_type: str,
    user_id: str | None,
    project_id: str | None,
    explicit_entity_id: str | None = None,
) -> dict[str, Any] | None:
    """
    Resolve referências antes de chamar
    o modelo.

    Regra:
    - ID explícito ganha;
    - senão usa entidade ativa;
    - se houver ambiguidade, não chuta.
    """

    if explicit_entity_id:

        candidates = search_memory(
            scope="project",
            user_id=user_id,
            project_id=project_id,
            memory_type="entity",
            key=entity_type,
            active_only=True,
            limit=100,
        )

        exact = [
            item
            for item in candidates
            if item["value"].get(
                "entity_id"
            ) == explicit_entity_id
        ]

        if len(exact) == 1:
            return exact[0]

        if len(exact) > 1:
            raise AmbiguousReferenceError(
                "Referência explícita possui "
                "mais de um registro ativo."
            )

        return None

    active = get_active_entity(
        entity_type=entity_type,
        user_id=user_id,
        project_id=project_id,
    )

    return active


# ============================================================
# REFERÊNCIA DE CAMPANHA
# ============================================================

def resolve_campaign_reference(
    *,
    user_id: str | None,
    project_id: str | None,
    campaign_id: str | None = None,
) -> dict[str, Any] | None:
    """
    Atalho determinístico para o primeiro
    teste real de continuidade.
    """

    return resolve_entity_reference(
        entity_type="campaign",
        user_id=user_id,
        project_id=project_id,
        explicit_entity_id=campaign_id,
    )


# ============================================================
# PACOTE RESUMIDO DE MEMÓRIA
# ============================================================

def build_memory_snapshot(
    *,
    user_id: str | None,
    project_id: str | None,
    session_id: str | None = None,
    specialist: str | None = None,
    limit_per_scope: int = 20,
) -> dict[str, Any]:
    """
    Retorna memória estruturada.

    NÃO é ainda o context packet final.
    O módulo de contexto decidirá o que
    realmente entra na janela do modelo.
    """

    snapshot: dict[str, Any] = {
        "user": [],
        "project": [],
        "session": [],
        "specialist": [],
    }

    if user_id is not None:

        snapshot["user"] = search_memory(
            scope="user",
            user_id=user_id,
            active_only=True,
            limit=limit_per_scope,
        )

    if project_id is not None:

        snapshot[
            "project"
        ] = search_memory(
            scope="project",
            user_id=user_id,
            project_id=project_id,
            active_only=True,
            limit=limit_per_scope,
        )

    if session_id is not None:

        snapshot[
            "session"
        ] = search_memory(
            scope="session",
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            active_only=True,
            limit=limit_per_scope,
        )

    if specialist is not None:

        snapshot[
            "specialist"
        ] = search_memory(
            scope="specialist",
            user_id=user_id,
            project_id=project_id,
            specialist=specialist,
            active_only=True,
            limit=limit_per_scope,
        )

    return snapshot


# ============================================================
# SELF TEST
# ============================================================

def self_test() -> dict[str, bool]:

    initialize_database()

    results: dict[str, bool] = {}

    suffix = uuid.uuid4().hex[:8]

    user_id = (
        f"user_memory_test_{suffix}"
    )

    project_id = (
        f"project_memory_test_{suffix}"
    )

    campaign_id = (
        f"campaign_{suffix}"
    )

    entity = register_entity(
        entity_type="campaign",
        entity_id=campaign_id,
        entity_name=(
            "Campanha Cafeteria Premium"
        ),
        user_id=user_id,
        project_id=project_id,
        promoted_by="control_plane",
    )

    results[
        "entity_registered"
    ] = (
        entity["value"]["entity_id"]
        == campaign_id
    )

    active = set_active_entity(
        entity_type="campaign",
        entity_id=campaign_id,
        entity_name=(
            "Campanha Cafeteria Premium"
        ),
        user_id=user_id,
        project_id=project_id,
        promoted_by="control_plane",
    )

    results[
        "active_entity_created"
    ] = (
        active["value"]["entity_id"]
        == campaign_id
    )

    resolved = (
        resolve_campaign_reference(
            user_id=user_id,
            project_id=project_id,
        )
    )

    results[
        "campaign_resolved"
    ] = (
        resolved is not None
        and
        resolved["value"][
            "entity_id"
        ] == campaign_id
    )

    blocked = False

    try:

        create_memory(
            scope="project",
            memory_type="unsafe_test",
            value={"x": 1},
            provenance={
                "source": "model"
            },
            promoted_by="queen",
            user_id=user_id,
            project_id=project_id,
        )

    except MemoryPromotionError:
        blocked = True

    results[
        "silent_ai_memory_blocked"
    ] = blocked

    snapshot = build_memory_snapshot(
        user_id=user_id,
        project_id=project_id,
    )

    results[
        "snapshot_has_project"
    ] = (
        len(
            snapshot["project"]
        ) >= 2
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
        "ChatCreova V23 Memory Service"
    )

    test_results = self_test()

    for name, passed in (
        test_results.items()
    ):

        print(
            f"{name}: "
            f"{'PASS' if passed else 'FAIL'}"
        )
