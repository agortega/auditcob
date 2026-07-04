"""Esquemas Pydantic para el pipeline de AuditCob.

Cada etapa se comunica a través de modelos tipados. AuditContext es el
acumulador que viaja por las 5 etapas, y AuditReport es la salida
final que se presenta al usuario.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ── Modelos de dominio primitivos ────────────────────────────────────────


class Turn(BaseModel):
    """Un intercambio individual en la conversación."""

    agente: str
    cliente: str


class Conversation(BaseModel):
    """Lista ordenada de turnos."""

    turns: list[Turn]


# ── Modelos de salida de cada etapa ──────────────────────────────────────


class SentimentResult(BaseModel):
    """Salida de la Etapa 1: sentimiento por rol más narrativa de evolución."""

    agent_sentiment: str = Field(
        ..., description="profesional | agresivo | neutral"
    )
    client_sentiment: str = Field(
        ..., description="cooperativo | resistente | neutral"
    )
    evolution: list[str] = Field(
        ..., description="Cómo evolucionó el estado de ánimo de la conversación"
    )


class BadPractice(BaseModel):
    """Un hallazgo de mala práctica con severidad, cita y recomendación."""

    practice: str
    severity: str = Field(..., description="alta | media | baja")
    citation: str
    recommendation: str


class RatingResult(BaseModel):
    """Salida de la Etapa 3: puntaje numérico, nivel y explicación."""

    score: int = Field(..., ge=0, le=100)
    level: str = Field(..., description="excelente | buena | regular | mala")
    explanation: str


class SummaryResult(BaseModel):
    """Salida de las Etapas 4 y 5: resumen ejecutivo y oportunidades de mejora."""

    summary: str
    opportunities: list[str]


# ── Wrappers de respuesta del LLM (para etapas que devuelven listas) ─────


class BadPracticeResponse(BaseModel):
    """Wrapper usado por la Etapa 2 para parsear la respuesta del LLM."""

    bad_practices: list[BadPractice]


class SummaryResponse(BaseModel):
    """Wrapper usado por la Etapa 4 para la porción del resumen."""

    summary: str


class FeedbackResponse(BaseModel):
    """Wrapper usado por la Etapa 5 para las oportunidades de mejora."""

    opportunities: list[str]


# ── Acumulador del pipeline y reporte final ──────────────────────────────


class AuditContext(BaseModel):
    """Acumulador mutable que atraviesa todas las etapas del pipeline.

    Cada etapa lee lo que necesita y escribe su resultado en el campo
    correspondiente. ``conversation`` se establece una vez desde el parser.
    """

    conversation: Conversation
    sentiment: Optional[SentimentResult] = None
    bad_practices: Optional[list[BadPractice]] = None
    rating: Optional[RatingResult] = None
    summary: Optional[SummaryResult] = None


class AuditReport(BaseModel):
    """Salida final presentada vía Streamlit — una vista plana y presentable."""

    total_turns: int
    sentiment: Optional[SentimentResult] = None
    bad_practices: Optional[list[BadPractice]] = None
    rating: Optional[RatingResult] = None
    summary: Optional[SummaryResult] = None
