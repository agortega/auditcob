"""Fixtures de pytest para la suite de tests de AuditCob.

Provee conversaciones de ejemplo, instancias de cliente simulado y
salidas de etapa pre-construidas.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from src.analyzer import OllamaClient
from src.models import (
    BadPractice,
    BadPracticeResponse,
    Conversation,
    FeedbackResponse,
    RatingResult,
    SentimentResult,
    SummaryResult,
    SummaryResponse,
    Turn,
)
from src.prompts import load_prompts

# ── Conversaciones de ejemplo ─────────────────────────────────────────────


@pytest.fixture
def ejemplo_json_valido() -> str:
    """Una conversación válida de 2 turnos como cadena JSON."""
    return (
        '[{"agente": "Buenos días, soy el gestor de cobranzas", '
        '"cliente": "Buenos días, no puedo pagar hoy"}, '
        '{"agente": "Entiendo, podemos ofrecerle un plan de pagos", '
        '"cliente": "Estaría bien, gracias"}]'
    )


@pytest.fixture
def ejemplo_json_sin_clave() -> str:
    """Un JSON con la clave ``cliente`` faltante."""
    return '[{"agente": "Hola", "otro": "test"}]'


@pytest.fixture
def ejemplo_json_vacio() -> str:
    """Una cadena vacía (JSON inválido)."""
    return ""


@pytest.fixture
def ejemplo_json_valores_vacios() -> str:
    """Un JSON con valores vacíos."""
    return '[{"agente": "", "cliente": ""}]'


@pytest.fixture
def ejemplo_conversacion() -> Conversation:
    """Una :class:`Conversation` parseada con 2 turnos."""
    return Conversation(
        turns=[
            Turn(agente="Buenos días", cliente="No puedo pagar"),
            Turn(
                agente="Podemos ofrecer un plan",
                cliente="Está bien, gracias",
            ),
        ]
    )


@pytest.fixture
def ejemplo_resultado_sentimiento() -> SentimentResult:
    return SentimentResult(
        agent_sentiment="profesional",
        client_sentiment="resistente",
        evolution=[
            "Apertura cordial",
            "Cliente se muestra reacio",
            "Cierre con acuerdo parcial",
        ],
    )


@pytest.fixture
def ejemplo_respuesta_mala_practica() -> BadPracticeResponse:
    return BadPracticeResponse(
        bad_practices=[
            BadPractice(
                practice="Presión indebida",
                severity="media",
                citation="Pague ya o tendrá problemas",
                recommendation="Usar tono más neutral",
            )
        ]
    )


@pytest.fixture
def ejemplo_resultado_calificacion() -> RatingResult:
    return RatingResult(
        score=65,
        level="regular",
        explanation="Tono profesional pero con presión innecesaria.",
    )


@pytest.fixture
def ejemplo_respuesta_resumen() -> SummaryResponse:
    return SummaryResponse(summary="Resumen ejecutivo de prueba.")


@pytest.fixture
def ejemplo_respuesta_retroalimentacion() -> FeedbackResponse:
    return FeedbackResponse(
        opportunities=[
            "Ofrecer planes de pago",
            "Mantener tono empático",
        ]
    )


# ── Fixtures de plantillas ────────────────────────────────────────────────


@pytest.fixture(scope="session")
def plantillas() -> dict[str, str]:
    """Cargar todas las plantillas de prompt una vez por sesión de tests."""
    return load_prompts()


# ── Fixture de cliente simulado ───────────────────────────────────────────


@pytest.fixture
def cliente_simulado() -> OllamaClient:
    """Un :class:`OllamaClient` inicializado en modo simulado."""
    return OllamaClient(mock=True)
