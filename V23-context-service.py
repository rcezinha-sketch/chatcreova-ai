"""
ChatCreova AI
V23-FUNDACAO-01

CONTEXT SERVICE

Responsabilidades:
- montar o Context Packet da Queen;
- preservar projeto/campanha ativa;
- controlar o orçamento de contexto;
- evitar envio desnecessário de histórico;
- priorizar informações importantes;
- registrar referências resolvidas;
- preparar entrada estruturada para o Qwen.

REGRA:
Contexto não é memória.

A memória persistente vem do Memory Service.
Este módulo apenas seleciona o que deve entrar
na janela de contexto do modelo.
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

MODEL_NAME = "qwen3.5:4b"

MODEL_CONTEXT_LIMIT = 4096

DEFAULT_OUTPUT_RESERVE = 950

DEFAULT_SAFETY_RESERVE = 200

DEFAULT_INPUT_BUDGET = (
    MODEL_CONTEXT_LIMIT
    - DEFAULT_OUTPUT_RESERVE
    - DEFAULT_SAFETY_RESERVE
)


# ============================================================
# ORÇAMENTO RECOMENDADO
# ============================================================

SECTION_BUDGETS = {
    "system": 300,
    "preferences": 150,
    "project": 300,
    "recent": 600,
    "retrieval": 900,
    "artifacts": 200,
    "task": 200,
}


# ============================================================
# PRIORIDADE
# ============================================================

SECTION_PRIORITY = (
    "system",
    "project",
    "task",
    "preferences",
    "recent",
    "retrieval",
    "artifacts",
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

memory_service = load_local_module(
    "chatcreova_v23_memory_service",
    "V23-memory-service.py",
)


database_connection = (
    database.database_connection
)

initialize_database = (
    database.initialize_database
)


# ============================================================
# EXCEÇÕES
# ============================================================

class ContextServiceError(Exception):
    """Erro-base do Context Service."""


class ContextBudgetError(
    ContextServiceError
):
    """Contexto excedeu limite seguro."""


class ContextReferenceError(
    ContextServiceError
):
    """Referência não pôde ser resolvida."""


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


# ============================================================
# ESTIMATIVA DE TOKENS
# ============================================================

def estimate_tokens(
    value: Any,
) -> int:
    """
    Estimativa conservadora.

    O tokenizer real poderá substituir
    esta função posteriormente.

    Para a fundação usamos aproximação
    para impedir crescimento sem limite.
    """

    if value is None:
        return 0

    if not isinstance(value, str):

        value = json.dumps(
            value,
            ensure_ascii=False,
        )

    if not value:
        return 0

    characters = len(value)

    estimated = max(
        1,
        characters // 3,
    )

    return estimated


# ============================================================
# CORTE DE TEXTO
# ============================================================

def trim_text_to_budget(
    text: str,
    token_budget: int,
) -> str:

    if token_budget <= 0:
        return ""

    if estimate_tokens(text) <= token_budget:
        return text

    max_chars = token_budget * 3

    if max_chars <= 20:
        return text[:max_chars]

    suffix = "\n[contexto reduzido]"

    available = (
        max_chars
        - len(suffix)
    )

    if available <= 0:
        return text[:max_chars]

    return (
        text[:available]
        + suffix
    )


# ============================================================
# NORMALIZAÇÃO DE MENSAGENS
# ============================================================

def normalize_messages(
    messages: list[dict[str, Any]]
    | None,
) -> list[dict[str, str]]:

    if not messages:
        return []

    normalized: list[
        dict[str, str]
    ] = []

    for item in messages:

        role = str(
            item.get(
                "role",
                "user",
            )
        ).strip()

        content = str(
            item.get(
                "content",
                "",
            )
        ).strip()

        if not content:
            continue

        if role not in {
            "user",
            "assistant",
            "system",
        }:
            role = "user"

        normalized.append(
            {
                "role": role,
                "content": content,
            }
        )

    return normalized


# ============================================================
# HISTÓRICO RECENTE
# ============================================================

def select_recent_messages(
    messages: list[dict[str, Any]]
    | None,
    token_budget: int,
) -> list[dict[str, str]]:
    """
    Seleciona mensagens começando
    pelas mais recentes.

    Não envia automaticamente toda
    a conversa para o modelo.
    """

    normalized = normalize_messages(
        messages
    )

    if not normalized:
        return []

    selected_reversed: list[
        dict[str, str]
    ] = []

    used = 0

    for item in reversed(normalized):

        cost = estimate_tokens(
            item["content"]
        )

        if used + cost <= token_budget:

            selected_reversed.append(
                item
            )

            used += cost

            continue

        remaining = (
            token_budget
            - used
        )

        if remaining > 20:

            trimmed = trim_text_to_budget(
                item["content"],
                remaining,
            )

            if trimmed:

                selected_reversed.append(
                    {
                        "role": item[
                            "role"
                        ],
                        "content": trimmed,
                    }
                )

        break

    selected_reversed.reverse()

    return selected_reversed


# ============================================================
# PREFERÊNCIAS
# ============================================================

def build_preferences_section(
    memory_snapshot: dict[str, Any],
) -> list[dict[str, Any]]:

    preferences: list[
        dict[str, Any]
    ] = []

    for memory in memory_snapshot.get(
        "user",
        [],
    ):

        if memory.get(
            "memory_type"
        ) in {
            "preference",
            "instruction",
            "profile_preference",
        }:

            preferences.append(
                {
                    "key": memory.get(
                        "key"
                    ),
                    "value": memory.get(
                        "value"
                    ),
                    "memory_id": (
                        memory.get(
                            "memory_id"
                        )
                    ),
                }
            )

    return preferences


# ============================================================
# PROJETO
# ============================================================

def build_project_section(
    *,
    project_id: str | None,
    project_name: str | None,
    memory_snapshot: dict[str, Any],
    resolved_refs: dict[str, Any],
) -> dict[str, Any]:

    project_memories: list[
        dict[str, Any]
    ] = []

    for memory in memory_snapshot.get(
        "project",
        [],
    ):

        memory_type = memory.get(
            "memory_type"
        )

        if memory_type in {
            "decision",
            "project_summary",
            "entity",
            "active_entity",
            "project_fact",
        }:

            project_memories.append(
                {
                    "memory_type": (
                        memory_type
                    ),
                    "key": memory.get(
                        "key"
                    ),
                    "value": memory.get(
                        "value"
                    ),
                    "memory_id": (
                        memory.get(
                            "memory_id"
                        )
                    ),
                }
            )

    return {
        "project_id": project_id,
        "project_name": project_name,
        "resolved_refs": resolved_refs,
        "memories": project_memories,
    }


# ============================================================
# DETECÇÃO DE REFERÊNCIA DE CAMPANHA
# ============================================================

CAMPAIGN_REFERENCE_PHRASES = (
    "campanha anterior",
    "campanha que fizemos",
    "campanha que criamos",
    "essa campanha",
    "aquela campanha",
    "continue a campanha",
    "continuar a campanha",
    "continua a campanha",
    "mesma campanha",
    "campanha acima",
    "campanha anterior que",
)


def mentions_campaign_reference(
    text: str,
) -> bool:

    lowered = text.lower()

    return any(
        phrase in lowered
        for phrase in (
            CAMPAIGN_REFERENCE_PHRASES
        )
    )


# ============================================================
# RESOLUÇÃO DE REFERÊNCIAS
# ============================================================

def resolve_references(
    *,
    user_text: str,
    user_id: str | None,
    project_id: str | None,
    explicit_campaign_id: (
        str | None
    ) = None,
) -> dict[str, Any]:

    resolved: dict[
        str,
        Any,
    ] = {}

    needs_campaign = (
        explicit_campaign_id
        is not None
        or
        mentions_campaign_reference(
            user_text
        )
    )

    if not needs_campaign:
        return resolved

    try:

        campaign = (
            memory_service
            .resolve_campaign_reference(
                user_id=user_id,
                project_id=project_id,
                campaign_id=(
                    explicit_campaign_id
                ),
            )
        )

    except (
        memory_service
        .AmbiguousReferenceError
    ) as exc:

        raise ContextReferenceError(
            "A referência à campanha "
            "é ambígua."
        ) from exc

    if campaign is None:

        raise ContextReferenceError(
            "O usuário fez referência "
            "a uma campanha, mas nenhuma "
            "campanha correspondente foi "
            "encontrada no projeto."
        )

    resolved["campaign"] = {
        "memory_id": (
            campaign["memory_id"]
        ),
        "entity_id": (
            campaign["value"].get(
                "entity_id"
            )
        ),
        "entity_name": (
            campaign["value"].get(
                "entity_name"
            )
        ),
        "last_task_id": (
            campaign["value"].get(
                "last_task_id"
            )
        ),
        "last_artifact_id": (
            campaign["value"].get(
                "last_artifact_id"
            )
        ),
        "extra": (
            campaign["value"].get(
                "extra",
                {},
            )
        ),
    }

    return resolved


# ============================================================
# TAREFA ATUAL
# ============================================================

def build_task_section(
    *,
    task_id: str | None,
    objective: str,
    specialist: str | None,
    constraints: dict[str, Any]
    | None,
) -> dict[str, Any]:

    return {
        "task_id": task_id,
        "objective": objective,
        "specialist": specialist,
        "constraints": (
            constraints or {}
        ),
    }


# ============================================================
# ARTEFATOS REFERENCIADOS
# ============================================================

def build_artifacts_section(
    artifacts: list[
        dict[str, Any]
    ]
    | None,
) -> list[dict[str, Any]]:

    if not artifacts:
        return []

    result: list[
        dict[str, Any]
    ] = []

    for artifact in artifacts:

        result.append(
            {
                "artifact_id": (
                    artifact.get(
                        "artifact_id"
                    )
                ),
                "type": artifact.get(
                    "type"
                ),
                "status": artifact.get(
                    "status"
                ),
                "verify_status": (
                    artifact.get(
                        "verify_status"
                    )
                ),
                "result_ref": (
                    artifact.get(
                        "result_ref"
                    )
                ),
                "metadata": (
                    artifact.get(
                        "metadata",
                        {},
                    )
                ),
            }
        )

    return result


# ============================================================
# RETRIEVAL
# ============================================================

def normalize_retrieval(
    retrieval: list[
        dict[str, Any]
    ]
    | None,
) -> list[dict[str, Any]]:

    if not retrieval:
        return []

    normalized: list[
        dict[str, Any]
    ] = []

    for item in retrieval:

        content = str(
            item.get(
                "content",
                "",
            )
        ).strip()

        if not content:
            continue

        normalized.append(
            {
                "source": item.get(
                    "source"
                ),
                "content": content,
                "score": item.get(
                    "score"
                ),
                "metadata": item.get(
                    "metadata",
                    {},
                ),
            }
        )

    return normalized


# ============================================================
# REDUÇÃO DE SEÇÃO
# ============================================================

def reduce_value_to_budget(
    value: Any,
    budget: int,
) -> Any:

    if budget <= 0:
        return None

    encoded = json.dumps(
        value,
        ensure_ascii=False,
    )

    if estimate_tokens(
        encoded
    ) <= budget:
        return value

    return {
        "reduced": True,
        "content": trim_text_to_budget(
            encoded,
            budget,
        ),
    }


# ============================================================
# CONTAGEM DAS SEÇÕES
# ============================================================

def section_token_usage(
    sections: dict[str, Any],
) -> dict[str, int]:

    usage: dict[str, int] = {}

    for name, value in (
        sections.items()
    ):

        usage[name] = (
            estimate_tokens(
                json.dumps(
                    value,
                    ensure_ascii=False,
                )
            )
        )

    return usage


# ============================================================
# APLICAÇÃO DOS LIMITES
# ============================================================

def apply_section_budgets(
    sections: dict[str, Any],
) -> dict[str, Any]:

    reduced: dict[
        str,
        Any,
    ] = {}

    for section_name in (
        SECTION_PRIORITY
    ):

        value = sections.get(
            section_name
        )

        budget = SECTION_BUDGETS.get(
            section_name,
            100,
        )

        if section_name == "recent":

            if isinstance(
                value,
                list,
            ):

                reduced[
                    section_name
                ] = (
                    select_recent_messages(
                        value,
                        budget,
                    )
                )

            else:

                reduced[
                    section_name
                ] = []

            continue

        reduced[
            section_name
        ] = reduce_value_to_budget(
            value,
            budget,
        )

    return reduced


# ============================================================
# LIMITE GLOBAL
# ============================================================

def enforce_global_budget(
    sections: dict[str, Any],
    max_input_tokens: int,
) -> dict[str, Any]:
    """
    Se ainda exceder o limite global,
    reduz seções de menor prioridade.

    Projeto nunca é descartado
    silenciosamente.
    """

    working = dict(sections)

    def total() -> int:

        return sum(
            section_token_usage(
                working
            ).values()
        )

    if total() <= max_input_tokens:
        return working

    removable_order = (
        "artifacts",
        "retrieval",
        "recent",
        "preferences",
    )

    for name in removable_order:

        if total() <= max_input_tokens:
            break

        value = working.get(name)

        current_tokens = (
            estimate_tokens(
                json.dumps(
                    value,
                    ensure_ascii=False,
                )
            )
        )

        if current_tokens <= 0:
            continue

        overflow = (
            total()
            - max_input_tokens
        )

        target = max(
            0,
            current_tokens
            - overflow
            - 10,
        )

        working[name] = (
            reduce_value_to_budget(
                value,
                target,
            )
        )

    if total() > max_input_tokens:

        task_tokens = (
            estimate_tokens(
                json.dumps(
                    working.get(
                        "task"
                    ),
                    ensure_ascii=False,
                )
            )
        )

        overflow = (
            total()
            - max_input_tokens
        )

        target = max(
            80,
            task_tokens
            - overflow,
        )

        working["task"] = (
            reduce_value_to_budget(
                working.get(
                    "task"
                ),
                target,
            )
        )

    if total() > max_input_tokens:

        raise ContextBudgetError(
            "Context Packet continua "
            "acima do limite seguro "
            "mesmo após redução."
        )

    return working


# ============================================================
# SYSTEM SECTION
# ============================================================

def default_system_section() -> dict[
    str,
    Any,
]:

    return {
        "assistant": "Queen",
        "platform": "ChatCreova AI",
        "version": "V23-FUNDACAO-01",
        "model": MODEL_NAME,
        "rules": [
            (
                "Use somente o contexto "
                "fornecido para referências "
                "de projeto."
            ),
            (
                "Não invente artefatos, "
                "execuções ou resultados."
            ),
            (
                "Não declare uma tarefa "
                "concluída por conta própria."
            ),
            (
                "Quando houver entidade "
                "resolvida, preserve seu ID."
            ),
        ],
    }


# ============================================================
# CRIAÇÃO DO CONTEXT PACKET
# ============================================================

def build_context_packet(
    *,
    user_text: str,
    user_id: str | None,
    project_id: str | None,
    project_name: str | None = None,
    session_id: str | None = None,
    task_id: str | None = None,
    specialist: str | None = None,
    constraints: dict[str, Any]
    | None = None,
    recent_messages: list[
        dict[str, Any]
    ]
    | None = None,
    retrieval: list[
        dict[str, Any]
    ]
    | None = None,
    artifacts: list[
        dict[str, Any]
    ]
    | None = None,
    explicit_campaign_id: (
        str | None
    ) = None,
    system_section: dict[
        str,
        Any,
    ]
    | None = None,
    max_input_tokens: int = (
        DEFAULT_INPUT_BUDGET
    ),
) -> dict[str, Any]:
    """
    Monta o pacote determinístico
    enviado para a camada de geração.
    """

    if not user_text.strip():

        raise ValueError(
            "user_text não pode ser vazio."
        )

    if max_input_tokens <= 0:

        raise ContextBudgetError(
            "max_input_tokens inválido."
        )

    initialize_database()

    resolved_refs = resolve_references(
        user_text=user_text,
        user_id=user_id,
        project_id=project_id,
        explicit_campaign_id=(
            explicit_campaign_id
        ),
    )

    memory_snapshot = (
        memory_service
        .build_memory_snapshot(
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            specialist=specialist,
        )
    )

    raw_sections = {
        "system": (
            system_section
            or default_system_section()
        ),
        "preferences": (
            build_preferences_section(
                memory_snapshot
            )
        ),
        "project": (
            build_project_section(
                project_id=project_id,
                project_name=project_name,
                memory_snapshot=(
                    memory_snapshot
                ),
                resolved_refs=(
                    resolved_refs
                ),
            )
        ),
        "recent": (
            recent_messages or []
        ),
        "retrieval": (
            normalize_retrieval(
                retrieval
            )
        ),
        "artifacts": (
            build_artifacts_section(
                artifacts
            )
        ),
        "task": (
            build_task_section(
                task_id=task_id,
                objective=user_text,
                specialist=specialist,
                constraints=constraints,
            )
        ),
    }

    budgeted = apply_section_budgets(
        raw_sections
    )

    final_sections = (
        enforce_global_budget(
            budgeted,
            max_input_tokens,
        )
    )

    usage = section_token_usage(
        final_sections
    )

    total_input_tokens = sum(
        usage.values()
    )

    packet = {
        "context_packet_id": (
            new_id("context")
        ),
        "schema_version": 1,
        "created_at": utc_now(),
        "model": MODEL_NAME,
        "model_context_limit": (
            MODEL_CONTEXT_LIMIT
        ),
        "max_input_tokens": (
            max_input_tokens
        ),
        "output_reserve": (
            DEFAULT_OUTPUT_RESERVE
        ),
        "safety_reserve": (
            DEFAULT_SAFETY_RESERVE
        ),
        "estimated_input_tokens": (
            total_input_tokens
        ),
        "token_usage_by_section": (
            usage
        ),
        "resolved_refs": (
            resolved_refs
        ),
        "sections": (
            final_sections
        ),
    }

    return packet


# ============================================================
# CONVERSÃO PARA MENSAGENS DO MODELO
# ============================================================

def context_packet_to_messages(
    packet: dict[str, Any],
) -> list[dict[str, str]]:
    """
    Converte Context Packet em mensagens
    que poderão ser usadas pelo gateway
    do Ollama.
    """

    sections = packet.get(
        "sections",
        {},
    )

    system_payload = {
        "system": sections.get(
            "system"
        ),
        "preferences": sections.get(
            "preferences"
        ),
        "project": sections.get(
            "project"
        ),
        "retrieval": sections.get(
            "retrieval"
        ),
        "artifacts": sections.get(
            "artifacts"
        ),
    }

    messages: list[
        dict[str, str]
    ] = [
        {
            "role": "system",
            "content": json.dumps(
                system_payload,
                ensure_ascii=False,
                indent=2,
            ),
        }
    ]

    recent = sections.get(
        "recent"
    )

    if isinstance(recent, list):

        for item in recent:

            if not isinstance(
                item,
                dict,
            ):
                continue

            role = item.get(
                "role"
            )

            content = item.get(
                "content"
            )

            if (
                role in {
                    "user",
                    "assistant",
                    "system",
                }
                and
                isinstance(
                    content,
                    str,
                )
                and
                content.strip()
            ):

                messages.append(
                    {
                        "role": role,
                        "content": content,
                    }
                )

    task = sections.get(
        "task"
    )

    if isinstance(task, dict):

        objective = task.get(
            "objective"
        )

    else:

        objective = None

    if objective:

        messages.append(
            {
                "role": "user",
                "content": str(
                    objective
                ),
            }
        )

    return messages


# ============================================================
# RESUMO PARA LOG
# ============================================================

def packet_summary(
    packet: dict[str, Any],
) -> dict[str, Any]:

    return {
        "context_packet_id": (
            packet.get(
                "context_packet_id"
            )
        ),
        "model": packet.get(
            "model"
        ),
        "estimated_input_tokens": (
            packet.get(
                "estimated_input_tokens"
            )
        ),
        "max_input_tokens": (
            packet.get(
                "max_input_tokens"
            )
        ),
        "resolved_refs": (
            packet.get(
                "resolved_refs",
                {},
            )
        ),
        "token_usage_by_section": (
            packet.get(
                "token_usage_by_section",
                {},
            )
        ),
    }


# ============================================================
# TESTE DE CONTINUIDADE
# ============================================================

def self_test() -> dict[str, bool]:

    initialize_database()

    results: dict[
        str,
        bool,
    ] = {}

    suffix = uuid.uuid4().hex[:8]

    user_id = (
        f"context_user_{suffix}"
    )

    project_id = (
        f"context_project_{suffix}"
    )

    campaign_id = (
        f"context_campaign_{suffix}"
    )

    memory_service.register_entity(
        entity_type="campaign",
        entity_id=campaign_id,
        entity_name=(
            "Campanha Cafeteria Premium"
        ),
        user_id=user_id,
        project_id=project_id,
        promoted_by="control_plane",
    )

    memory_service.set_active_entity(
        entity_type="campaign",
        entity_id=campaign_id,
        entity_name=(
            "Campanha Cafeteria Premium"
        ),
        user_id=user_id,
        project_id=project_id,
        extra={
            "theme": "cafeteria",
            "format": "reel",
        },
        promoted_by="control_plane",
    )

    packet = build_context_packet(
        user_text=(
            "Continue a campanha anterior "
            "e crie mais três títulos."
        ),
        user_id=user_id,
        project_id=project_id,
        project_name=(
            "Projeto Cafeteria"
        ),
        specialist=(
            "analista_texto"
        ),
        recent_messages=[
            {
                "role": "user",
                "content": (
                    "Crie uma campanha "
                    "para uma cafeteria."
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "Campanha criada."
                ),
            },
        ],
    )

    campaign_ref = (
        packet[
            "resolved_refs"
        ].get(
            "campaign"
        )
    )

    results[
        "campaign_reference_resolved"
    ] = (
        campaign_ref is not None
        and
        campaign_ref.get(
            "entity_id"
        ) == campaign_id
    )

    results[
        "project_preserved"
    ] = (
        packet[
            "sections"
        ][
            "project"
        ][
            "project_id"
        ]
        == project_id
    )

    results[
        "budget_respected"
    ] = (
        packet[
            "estimated_input_tokens"
        ]
        <= packet[
            "max_input_tokens"
        ]
    )

    messages = (
        context_packet_to_messages(
            packet
        )
    )

    results[
        "messages_created"
    ] = (
        len(messages) >= 2
    )

    results[
        "user_objective_present"
    ] = any(
        message["role"] == "user"
        and
        "Continue a campanha anterior"
        in message["content"]
        for message in messages
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
        "Context Service"
    )

    test_results = self_test()

    for name, passed in (
        test_results.items()
    ):

        print(
            f"{name}: "
            f"{'PASS' if passed else 'FAIL'}"
        )
