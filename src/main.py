"""Orquestador del pipeline.

Carga las variables de entorno y las plantillas de prompt, inicializa el
cliente Ollama, construye las 5 etapas del pipeline y las ejecuta
secuencialmente contra una conversación parseada.
El resultado es un :class:`AuditReport` plano.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

from src.analyzer import OllamaClient
from src.models import AuditContext, AuditReport, Conversation
from src.parser import parse_conversation
from src.prompts import load_prompts
from src.stages import StageFn
from src.stages.bad_practices import build_stage as build_bad_practices
from src.stages.feedback import build_stage as build_feedback
from src.stages.rating import build_stage as build_rating
from src.stages.sentiment import build_stage as build_sentiment
from src.stages.summary import build_stage as build_summary

# ── Registro de etapas del pipeline ───────────────────────────────────────

StageBuilder = tuple[str, StageFn]
"""Nombre legible más una función de etapa invocable."""

STAGES: list[StageBuilder] = [
    ("sentiment", build_sentiment),
    ("bad_practices", build_bad_practices),
    ("rating", build_rating),
    ("summary", build_summary),
    ("feedback", build_feedback),
]


def run_pipeline(
    raw_json: str,
    mock: bool = False,
    *,
    _client: OllamaClient | None = None,
    _prompts: dict[str, str] | None = None,
) -> AuditReport:
    """Parsear la entrada, ejecutar las 5 etapas del pipeline y retornar un reporte.

    Parameters
    ----------
    raw_json:
        Cadena JSON que representa una conversación
        (``list[dict[str, str]]`` con claves ``"agente"`` / ``"cliente"``).
    mock:
        Cuando es ``True``, usa respuestas simuladas del LLM (sin llamadas de red).
    _client, _prompts:
        Uso interno — permite sobreescribir cliente/plantillas para pruebas.

    Returns
    -------
    AuditReport
        El reporte final con las salidas de todas las etapas.

    Raises
    ------
    src.parser.ParseError
        Si el JSON de entrada es inválido.
    RuntimeError
        Si la llamada al LLM falla persistentemente.
    """
    # 1. Parsear
    conversation: Conversation = parse_conversation(raw_json)

    # 2. Inicializar cliente y plantillas
    client = _client or _build_client(mock=mock)
    plantillas = _prompts or _build_prompts()

    # 3. Construir etapas
    etapas: list[StageFn] = [builder(plantillas) for _, builder in STAGES]

    # 4. Crear acumulador
    ctx = AuditContext(conversation=conversation)

    # 5. Ejecutar etapas secuencialmente
    for etapa in etapas:
        ctx = etapa(ctx, client)

    # 6. Construir reporte
    return AuditReport(
        total_turns=len(ctx.conversation.turns),
        sentiment=ctx.sentiment,
        bad_practices=ctx.bad_practices,
        rating=ctx.rating,
        summary=ctx.summary,
    )


def _build_client(*, mock: bool = False) -> OllamaClient:
    """Crear un :class:`OllamaClient` a partir de variables de entorno."""
    load_dotenv()
    return OllamaClient(
        host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud"),
        mock=mock,
    )


def _build_prompts() -> dict[str, str]:
    """Cargar las plantillas de prompt desde el disco."""
    return load_prompts()


# ── Punto de entrada CLI ──────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    SAMPLE = (
        '[{"agente": "Señor, debe pagar hoy", '
        '"cliente": "disculpeme pero no puedo pagar"}, '
        '{"agente": "Lo siento pero no somos caridad", '
        '"cliente": "..."}]'
    )

    mock_mode = "--mock" in sys.argv
    json_input = SAMPLE if len(sys.argv) <= 1 or mock_mode else sys.argv[1]

    report = run_pipeline(json_input, mock=mock_mode)
    print(report.model_dump_json(indent=2))
