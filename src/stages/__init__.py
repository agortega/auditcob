"""Tipo de función de etapa del pipeline y utilidades de construcción.

Toda etapa tiene la misma firma:

    ``StageFn = Callable[[AuditContext, OllamaClient], AuditContext``

Esto permite que el orquestador almacene las etapas como una lista simple
y las ejecute secuencialmente con un bucle ``for``.
"""

from __future__ import annotations

from collections.abc import Callable

from src.analyzer import OllamaClient
from src.models import AuditContext

StageFn = Callable[[AuditContext, OllamaClient], AuditContext]
"""Alias de tipo para cualquier función de etapa del pipeline."""


def format_conversation(ctx: AuditContext) -> str:
    """Construir una transcripción legible a partir de los turnos de la conversación."""
    lineas: list[str] = []
    for i, turno in enumerate(ctx.conversation.turns, 1):
        lineas.append(f"Turno {i}:")
        lineas.append(f"  Agente: {turno.agente}")
        lineas.append(f"  Cliente: {turno.cliente}")
    return "\n".join(lineas)
