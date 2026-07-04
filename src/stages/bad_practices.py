"""Etapa 2 — Detección de malas prácticas.

Analiza la conversación en busca de amenazas, presión, groserías u otras
conductas no profesionales. Almacena los hallazgos en
``AuditContext.bad_practices``.
"""

from __future__ import annotations

from src.analyzer import OllamaClient
from src.models import AuditContext, BadPracticeResponse
from src.stages import StageFn, format_conversation


def build_stage(prompts: dict[str, str]) -> StageFn:
    """Crear la etapa de detección de malas prácticas.

    Parameters
    ----------
    prompts:
        Debe contener la clave ``"bad_practices"``.
    """

    def stage(ctx: AuditContext, client: OllamaClient) -> AuditContext:
        prompt = prompts["bad_practices"].format(
            conversation=format_conversation(ctx)
        )
        resultado = client.generate(prompt, BadPracticeResponse)
        ctx.bad_practices = resultado.bad_practices
        return ctx

    return stage
