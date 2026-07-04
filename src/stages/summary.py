"""Etapa 4 — Resumen de la conversación.

Genera un resumen ejecutivo de la conversación. Almacena el resultado
como ``AuditContext.summary.summary`` (el campo ``opportunities`` queda
vacío para que la Etapa 5 lo complete).
"""

from __future__ import annotations

from src.analyzer import OllamaClient
from src.models import AuditContext, SummaryResponse, SummaryResult
from src.stages import StageFn, format_conversation


def build_stage(prompts: dict[str, str]) -> StageFn:
    """Crear la etapa de resumen.

    Parameters
    ----------
    prompts:
        Debe contener la clave ``"summary"``.
    """

    def stage(ctx: AuditContext, client: OllamaClient) -> AuditContext:
        prompt = prompts["summary"].format(
            conversation=format_conversation(ctx)
        )
        resultado = client.generate(prompt, SummaryResponse)
        ctx.summary = SummaryResult(
            summary=resultado.summary, opportunities=[]
        )
        return ctx

    return stage
