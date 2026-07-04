"""Tests para las 5 etapas del pipeline.

Cada etapa se prueba con un cliente simulado y una conversación de
ejemplo. El test verifica que el campo correcto del contexto se
complete.
"""

from __future__ import annotations

from src.models import (
    AuditContext,
    Conversation,
)
from src.stages.bad_practices import build_stage as build_bad_practices
from src.stages.feedback import build_stage as build_feedback
from src.stages.rating import build_stage as build_rating
from src.stages.sentiment import build_stage as build_sentiment
from src.stages.summary import build_stage as build_summary


def _crear_contexto(conversation: Conversation) -> AuditContext:
    """Ayudante: crear un AuditContext con solo la conversación."""
    return AuditContext(conversation=conversation)


class TestEtapaSentimiento:
    """Etapa 1 — Análisis de sentimiento."""

    def test_completa_sentimiento(
        self, plantillas: dict[str, str], cliente_simulado, ejemplo_conversacion
    ) -> None:
        stage = build_sentiment(plantillas)
        ctx = _crear_contexto(ejemplo_conversacion)
        resultado = stage(ctx, cliente_simulado)

        assert resultado.sentiment is not None
        assert resultado.sentiment.agent_sentiment in (
            "profesional",
            "agresivo",
            "neutral",
        )
        assert isinstance(resultado.sentiment.evolution, list)


class TestEtapaMalasPracticas:
    """Etapa 2 — Detección de malas prácticas."""

    def test_completa_malas_practicas(
        self, plantillas: dict[str, str], cliente_simulado, ejemplo_conversacion
    ) -> None:
        stage = build_bad_practices(plantillas)
        ctx = _crear_contexto(ejemplo_conversacion)
        resultado = stage(ctx, cliente_simulado)

        assert resultado.bad_practices is not None
        assert len(resultado.bad_practices) > 0
        bp = resultado.bad_practices[0]
        assert bp.practice != ""
        assert bp.severity in ("alta", "media", "baja")
        assert bp.citation != ""
        assert bp.recommendation != ""


class TestEtapaCalificacion:
    """Etapa 3 — Calificación de calidad."""

    def test_completa_calificacion(
        self, plantillas: dict[str, str], cliente_simulado, ejemplo_conversacion
    ) -> None:
        stage = build_rating(plantillas)
        ctx = _crear_contexto(ejemplo_conversacion)
        resultado = stage(ctx, cliente_simulado)

        assert resultado.rating is not None
        assert 0 <= resultado.rating.score <= 100
        assert resultado.rating.level in ("excelente", "buena", "regular", "mala")
        assert resultado.rating.explanation != ""


class TestEtapaResumen:
    """Etapa 4 — Resumen de la conversación."""

    def test_completa_resumen(
        self, plantillas: dict[str, str], cliente_simulado, ejemplo_conversacion
    ) -> None:
        stage = build_summary(plantillas)
        ctx = _crear_contexto(ejemplo_conversacion)
        resultado = stage(ctx, cliente_simulado)

        assert resultado.summary is not None
        assert resultado.summary.summary != ""
        # opportunities debe empezar vacío (la Etapa 5 los completa)
        assert resultado.summary.opportunities == []


class TestEtapaRetroalimentacion:
    """Etapa 5 — Oportunidades de mejora."""

    def test_completa_retroalimentacion(
        self, plantillas: dict[str, str], cliente_simulado, ejemplo_conversacion
    ) -> None:
        # La Etapa 4 debe ejecutarse primero para que ctx.summary exista
        summary_stage = build_summary(plantillas)
        feedback_stage = build_feedback(plantillas)

        ctx = _crear_contexto(ejemplo_conversacion)
        ctx = summary_stage(ctx, cliente_simulado)
        ctx = feedback_stage(ctx, cliente_simulado)

        assert ctx.summary is not None
        assert len(ctx.summary.opportunities) > 0
        assert all(isinstance(o, str) for o in ctx.summary.opportunities)


class TestPipelineCompleto:
    """Las 5 etapas juntas con cliente simulado."""

    def test_todas_las_etapas_completas(
        self, plantillas: dict[str, str], cliente_simulado, ejemplo_conversacion
    ) -> None:
        etapas = [
            build_sentiment(plantillas),
            build_bad_practices(plantillas),
            build_rating(plantillas),
            build_summary(plantillas),
            build_feedback(plantillas),
        ]
        ctx = _crear_contexto(ejemplo_conversacion)

        for etapa in etapas:
            ctx = etapa(ctx, cliente_simulado)

        # Todo debería estar completo
        assert ctx.sentiment is not None
        assert ctx.bad_practices is not None and len(ctx.bad_practices) > 0
        assert ctx.rating is not None
        assert ctx.summary is not None
        assert ctx.summary.summary != ""
        assert len(ctx.summary.opportunities) > 0
