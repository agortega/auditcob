"""Etapa 5 — Oportunidades de mejora (retroalimentación).

Genera recomendaciones de mejora específicas y accionables para el agente
y las almacena en ``AuditContext.summary.opportunities``.
"""

from __future__ import annotations

from src.analyzer import OllamaClient
from src.models import AuditContext, FeedbackResponse
from src.stages import StageFn, format_conversation


def build_stage(prompts: dict[str, str]) -> StageFn:
    """Crear la etapa de retroalimentación.

    Parameters
    ----------
    prompts:
        Debe contener la clave ``"feedback"``.
    """

    def stage(ctx: AuditContext, client: OllamaClient) -> AuditContext:
        prompt = prompts["feedback"].format(
            conversation=format_conversation(ctx)
        )
        resultado = client.generate(prompt, FeedbackResponse)
        if ctx.summary is not None:
            ctx.summary.opportunities = resultado.opportunities
        return ctx

    return stage
