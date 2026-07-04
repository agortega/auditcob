"""Cliente HTTP para Ollama con reintentos, timeout y modo simulado.

La clase :class:`OllamaClient` es el único componente que habla con el LLM.
Cada etapa del pipeline recibe la misma instancia compartida del cliente.
"""

from __future__ import annotations

import json
import time
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

from src.models import (
    BadPracticeResponse,
    FeedbackResponse,
    RatingResult,
    SentimentResult,
    SummaryResponse,
)

# ── Respuestas mock por defecto ───────────────────────────────────────────
# Cada tipo de esquema mapea a una instancia válida que se retorna cuando
# ``mock=True``.

MOCK_RESPONSES: dict[type[BaseModel], BaseModel] = {
    SentimentResult: SentimentResult(
        agent_sentiment="profesional",
        client_sentiment="resistente",
        evolution=[
            "El agente inicia la conversación con un saludo cordial.",
            "El cliente se muestra evasivo ante la solicitud de pago.",
            "El agente mantiene un tono profesional pese a la resistencia.",
        ],
    ),
    BadPracticeResponse: BadPracticeResponse(
        bad_practices=[
            {
                "practice": "Presión indebida",
                "severity": "media",
                "citation": "Pague ya o tendrá problemas serios",
                "recommendation": "Utilizar lenguaje neutral y evitar "
                "amenazas implícitas.",
            }
        ]
    ),
    RatingResult: RatingResult(
        score=65,
        level="regular",
        explanation="La conversación se mantuvo profesional pero "
        "se detectaron momentos de presión que reducen la calidad.",
    ),
    SummaryResponse: SummaryResponse(
        summary="Resumen ejecutivo de prueba generado por el mock.",
    ),
    FeedbackResponse: FeedbackResponse(
        opportunities=[
            "Ofrecer planes de pago desde el primer contacto.",
            "Mantener un tono empático ante la resistencia del cliente.",
            "Evitar frases que puedan interpretarse como presión.",
        ]
    ),
}


class OllamaClient:
    """Cliente HTTP para la API de generación de Ollama.

    Parameters
    ----------
    host:
        URL del servidor Ollama (ej. ``http://localhost:11434``).
    model:
        Nombre del modelo (ej. ``gemma4:31b-cloud``).
    mock:
        Cuando es ``True``, retorna respuestas prefijadas sin llamadas de red.
    timeout:
        Timeout de la solicitud en segundos.
    max_retries:
        Cantidad máxima de reintentos para errores de servidor (5xx).
    """

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "gemma4:31b-cloud",
        mock: bool = False,
        timeout: float = 120.0,
        max_retries: int = 3,
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.mock = mock
        self.timeout = timeout
        self.max_retries = max_retries
        self._http = httpx.Client(timeout=timeout)

    # ── API pública ─────────────────────────────────────────────────────

    def generate(self, prompt: str, schema: type[T]) -> T:
        """Enviar un prompt a Ollama y parsear la respuesta en *schema*.

        Reintenta en errores 5xx con backoff exponencial (máx. 3 intentos).
        Los errores 4xx NO se reintentan — se lanzan de inmediato.

        Parameters
        ----------
        prompt:
            El texto completo del prompt (normalmente cargado desde un
            archivo ``.txt``).
        schema:
            Una clase de modelo Pydantic que valida y parsea la respuesta.

        Returns
        -------
        T
            Una instancia de *schema* con los datos de respuesta del LLM.

        Raises
        ------
        RuntimeError
            En errores persistentes del servidor o solicitudes inválidas.
        """
        if self.mock:
            return self._mock_generate(schema)

        ultimo_error: Exception | None = None

        for intento in range(1, self.max_retries + 1):
            try:
                respuesta = self._http.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                    },
                )
            except httpx.TimeoutException as exc:
                ultimo_error = RuntimeError(
                    f"Timeout tras {intento} intento(s)."
                )
                if intento < self.max_retries:
                    self._esperar(intento)
                    continue
                raise ultimo_error from exc

            except httpx.RequestError as exc:
                ultimo_error = RuntimeError(
                    f"Error de conexión con Ollama en {self.host}: {exc}"
                )
                if intento < self.max_retries:
                    self._esperar(intento)
                    continue
                raise ultimo_error from exc

            # 4xx — error del cliente, NO reintentar
            if 400 <= respuesta.status_code < 500:
                raise RuntimeError(
                    f"Error del cliente HTTP ({respuesta.status_code}): "
                    f"{respuesta.text[:200]}"
                )

            # 5xx — error del servidor, reintentar
            if respuesta.status_code >= 500:
                ultimo_error = RuntimeError(
                    f"Error del servidor ({respuesta.status_code}) tras "
                    f"{intento} intento(s): {respuesta.text[:200]}"
                )
                if intento < self.max_retries:
                    self._esperar(intento)
                    continue
                raise ultimo_error

            # 200 — éxito, parsear la respuesta
            try:
                cuerpo: dict[str, Any] = respuesta.json()
                texto_crudo: str = cuerpo.get("response", "")
                if not texto_crudo.strip():
                    raise ValueError("Respuesta vacía del modelo.")
                # Sacar los fences de Markdown si están presentes (```json ... ```)
                limpio = texto_crudo.strip()
                if limpio.startswith("```"):
                    # Sacar el fence de apertura (```json, ```, etc.)
                    primer_salto = limpio.find("\n")
                    if primer_salto != -1:
                        limpio = limpio[primer_salto + 1 :]
                    # Sacar el fence de cierre si está presente
                    if limpio.endswith("```"):
                        limpio = limpio[: limpio.rfind("```")]
                    limpio = limpio.strip()
                parseado: dict[str, Any] = json.loads(limpio)
                return schema(**parseado)
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                ultimo_error = RuntimeError(
                    f"Error al parsear respuesta JSON del modelo: {exc}"
                )
                if intento < self.max_retries:
                    self._esperar(intento)
                    continue
                raise ultimo_error

        # No debería llegar acá, pero satisface al type checker.
        raise RuntimeError("Falló la generación tras todos los reintentos.")

    # ── Ayudantes internos ───────────────────────────────────────────────

    def _mock_generate(self, schema: type[T]) -> T:
        """Retornar una respuesta prefijada para *schema*."""
        mock = MOCK_RESPONSES.get(schema)
        if mock is not None:
            return mock.model_copy(deep=True)  # type: ignore[return-value]
        mensaje = f"No hay respuesta mock para el esquema {schema.__name__}."
        raise RuntimeError(mensaje)

    @staticmethod
    def _esperar(intento: int) -> None:
        """Backoff exponencial: 1 s, 2 s, 4 s, …"""
        time.sleep(2 ** (intento - 1))
