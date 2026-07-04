"""Etapa 3 — Calificación de calidad.

Asigna un puntaje numérico (0–100), un nivel cualitativo y una
explicación basada en sentimiento, malas prácticas e intento de
resolución. Almacena el resultado en ``AuditContext.rating``.
"""

from __future__ import annotations

from src.analyzer import OllamaClient
from src.models import AuditContext, RatingResult
from src.stages import StageFn, format_conversation


def build_stage(prompts: dict[str, str]) -> StageFn:
    """Crear la etapa de calificación de calidad.

    Parameters
    ----------
    prompts:
        Debe contener la clave ``"rating"``.
    """

    def stage(ctx: AuditContext, client: OllamaClient) -> AuditContext:
        prompt = prompts["rating"].format(
            conversation=format_conversation(ctx)
        )
        ctx.rating = client.generate(prompt, RatingResult)
        return ctx

    return stage
