"""Etapa 1 — Análisis de sentimiento.

Lee la conversación, envía el prompt al LLM para obtener el sentimiento
por rol y la narrativa de evolución, y almacena el resultado en
``AuditContext.sentiment``.
"""

from __future__ import annotations

from src.analyzer import OllamaClient
from src.models import AuditContext, SentimentResult
from src.stages import StageFn, format_conversation


def build_stage(prompts: dict[str, str]) -> StageFn:
    """Crear la etapa de análisis de sentimiento.

    Parameters
    ----------
    prompts:
        Plantillas de prompt cargadas por ``src.prompts.load_prompts()``.
        Debe contener la clave ``"sentiment"``.
    """

    def stage(ctx: AuditContext, client: OllamaClient) -> AuditContext:
        prompt = prompts["sentiment"].format(
            conversation=format_conversation(ctx)
        )
        ctx.sentiment = client.generate(prompt, SentimentResult)
        return ctx

    return stage
