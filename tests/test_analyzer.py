"""Tests para :mod:`src.analyzer`.

Cubre los escenarios de especificación S1–S3 para la capacidad de
integración con Ollama:
- S1: Recuperación de errores 503
- S2: Modelo incorrecto (4xx) — NO se reintenta
- S3: Modo simulado retorna respuestas prefijadas
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest
from pydantic import BaseModel

from src.analyzer import OllamaClient
from src.models import SentimentResult


# ── Tests de modo simulado ────────────────────────────────────────────────


class TestModoSimulado:
    """Especificación S3 — Modo simulado."""

    def test_simulado_retorna_respuesta_tipeada(self) -> None:
        """S3: DADO simulado habilitado CUANDO se solicita ENTONCES respuesta prefijada."""
        client = OllamaClient(mock=True)
        resultado = client.generate("prompt", SentimentResult)
        assert isinstance(resultado, SentimentResult)
        assert resultado.agent_sentiment == "profesional"
        assert resultado.client_sentiment == "resistente"
        assert len(resultado.evolution) == 3

    def test_simulado_sin_llamadas_red(self) -> None:
        """S3: Modo simulado hace cero llamadas HTTP."""
        client = OllamaClient(mock=True)
        with patch.object(client, "_http") as mock_http:
            client.generate("prompt", SentimentResult)
            mock_http.post.assert_not_called()

    def test_simulado_esquema_desconocido_lanza_error(self) -> None:
        """Modo simulado lanza error cuando no hay respuesta registrada."""

        class ModeloDesconocido(BaseModel):
            x: int

        client = OllamaClient(mock=True)
        with pytest.raises(RuntimeError, match="No hay respuesta mock"):
            client.generate("prompt", ModeloDesconocido)


# ── Tests de lógica de reintentos ─────────────────────────────────────────


class TestReintentos:
    """Especificación S1 — Recuperación de errores de servidor."""

    def test_reintento_503_luego_exito(self) -> None:
        """S1: DADO 503→503→200 CUANDO se envía ENTONCES éxito en intento 3."""
        client = OllamaClient(mock=False, max_retries=3)
        respuestas = [
            httpx.Response(503, text="Service Unavailable"),
            httpx.Response(503, text="Service Unavailable"),
            httpx.Response(
                200,
                json={
                    "response": (
                        '{"agent_sentiment": "profesional", '
                        '"client_sentiment": "cooperativo", '
                        '"evolution": ["a", "b"]}'
                    )
                },
            ),
        ]
        mock_post = MagicMock(side_effect=respuestas)

        with patch.object(client, "_http") as mock_http:
            mock_http.post = mock_post
            resultado = client.generate("prompt", SentimentResult)

        assert isinstance(resultado, SentimentResult)
        assert mock_post.call_count == 3

    def test_reintentos_503_agotados(self) -> None:
        """Todos los reintentos agotados en 503 persistente lanza RuntimeError."""
        client = OllamaClient(mock=False, max_retries=2)
        mock_post = MagicMock(
            return_value=httpx.Response(503, text="Service Unavailable")
        )

        with patch.object(client, "_http") as mock_http:
            mock_http.post = mock_post
            with pytest.raises(RuntimeError, match="Error del servidor"):
                client.generate("prompt", SentimentResult)

        assert mock_post.call_count == 2


class TestSinReintentosEn4xx:
    """Especificación S2 — Errores de cliente NO se reintentan."""

    def test_404_no_se_reintenta(self) -> None:
        """Un 404 (modelo no encontrado) lanza de inmediato, sin reintento."""
        client = OllamaClient(mock=False)
        mock_post = MagicMock(
            return_value=httpx.Response(404, text="model not found")
        )

        with patch.object(client, "_http") as mock_http:
            mock_http.post = mock_post
            with pytest.raises(RuntimeError, match="Error del cliente"):
                client.generate("prompt", SentimentResult)

        assert mock_post.call_count == 1  # sin reintento

    def test_400_no_se_reintenta(self) -> None:
        """Un 400 (solicitud incorrecta) lanza de inmediato."""
        client = OllamaClient(mock=False)
        mock_post = MagicMock(
            return_value=httpx.Response(400, text="bad request")
        )

        with patch.object(client, "_http") as mock_http:
            mock_http.post = mock_post
            with pytest.raises(RuntimeError, match="Error del cliente"):
                client.generate("prompt", SentimentResult)

        assert mock_post.call_count == 1


# ── Tests de errores de red ──────────────────────────────────────────────


class TestErroresDeRed:
    """Errores a nivel de red también deben disparar reintentos."""

    def test_timeout_dispara_reintento(self) -> None:
        """TimeoutException causa reintento, luego lanza si es persistente."""
        client = OllamaClient(mock=False, max_retries=2)
        mock_post = MagicMock(side_effect=httpx.TimeoutException("timeout"))

        with patch.object(client, "_http") as mock_http:
            mock_http.post = mock_post
            with pytest.raises(RuntimeError, match="Timeout"):
                client.generate("prompt", SentimentResult)

        assert mock_post.call_count == 2
