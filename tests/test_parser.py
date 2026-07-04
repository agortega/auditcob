"""Tests para :mod:`src.parser`.

Cubre los escenarios de especificación S1–S3 para la capacidad de
parseo de conversaciones:
- S1: JSON válido
- S2: Claves inválidas / faltantes
- S3: Entrada vacía
"""

from __future__ import annotations

import pytest

from src.parser import ParseError, parse_conversation


class TestParseoConversacion:
    """Especificación S1 — JSON válido produce una Conversation."""

    def test_json_valido(self, ejemplo_json_valido: str) -> None:
        """S1: DADO JSON válido CUANDO el parser valida ENTONCES retorna lista parseada."""
        conv = parse_conversation(ejemplo_json_valido)
        assert len(conv.turns) == 2
        assert conv.turns[0].agente == "Buenos días, soy el gestor de cobranzas"
        assert conv.turns[0].cliente == "Buenos días, no puedo pagar hoy"
        assert conv.turns[1].agente == "Entiendo, podemos ofrecerle un plan de pagos"

    def test_turno_unico_valido(self) -> None:
        """Un solo turno válido también funciona."""
        raw = '[{"agente": "Hola", "cliente": "Chau"}]'
        conv = parse_conversation(raw)
        assert len(conv.turns) == 1
        assert conv.turns[0].agente == "Hola"

    def test_limpia_espacios(self) -> None:
        """Los valores deben limpiarse de espacios circundantes."""
        raw = '[{"agente": "  Hola  ", "cliente": "  Chau  "}]'
        conv = parse_conversation(raw)
        assert conv.turns[0].agente == "Hola"
        assert conv.turns[0].cliente == "Chau"

    def test_lista_vacia(self) -> None:
        """Una lista vacía ``[]`` produce una Conversation con cero turnos."""
        conv = parse_conversation("[]")
        assert len(conv.turns) == 0


class TestErroresParseo:
    """Especificación S2 — Claves inválidas o faltantes."""

    def test_sin_clave_cliente(self, ejemplo_json_sin_clave: str) -> None:
        """S2: DADO falta ``cliente`` CUANDO se valida ENTONCES error."""
        with pytest.raises(ParseError, match="Falta la clave 'cliente'"):
            parse_conversation(ejemplo_json_sin_clave)

    def test_sin_clave_agente(self) -> None:
        """Falta ``agente`` lanza ParseError."""
        raw = '[{"cliente": "test"}]'
        with pytest.raises(ParseError, match="Falta la clave 'agente'"):
            parse_conversation(raw)

    def test_agente_vacio(self, ejemplo_json_valores_vacios: str) -> None:
        """``agente`` vacío lanza ParseError."""
        with pytest.raises(ParseError, match="'agente' debe ser un texto no vacío"):
            parse_conversation(ejemplo_json_valores_vacios)

    def test_cliente_vacio(self) -> None:
        """``cliente`` vacío lanza ParseError."""
        raw = '[{"agente": "Hola", "cliente": "  "}]'
        with pytest.raises(ParseError, match="'cliente' debe ser un texto no vacío"):
            parse_conversation(raw)

    def test_no_es_lista(self) -> None:
        """Un dict (no lista) lanza ParseError."""
        raw = '{"agente": "Hola", "cliente": "Chau"}'
        with pytest.raises(ParseError, match="Se esperaba una lista"):
            parse_conversation(raw)

    def test_elemento_no_dict(self) -> None:
        """Una lista con un string en vez de dict lanza ParseError."""
        raw = '["hola"]'
        with pytest.raises(ParseError, match="no es un objeto"):
            parse_conversation(raw)

    def test_claves_extra_permitidas(self) -> None:
        """Claves extra más allá de ``agente``/``cliente`` se ignoran (no es error)."""
        raw = '[{"agente": "A", "cliente": "C", "extra": "x"}]'
        conv = parse_conversation(raw)
        assert len(conv.turns) == 1


class TestCasosBorde:
    """Especificación S3 — Entrada vacía y mal formada."""

    def test_cadena_vacia(self, ejemplo_json_vacio: str) -> None:
        """S3: DADO cadena vacía CUANDO se valida ENTONCES error de parseo."""
        with pytest.raises(ParseError, match="JSON inválido"):
            parse_conversation(ejemplo_json_vacio)

    def test_json_mal_formado(self) -> None:
        """JSON mal formado lanza ParseError."""
        with pytest.raises(ParseError, match="JSON inválido"):
            parse_conversation("{malformed")

    def test_json_numerico(self) -> None:
        """Un número JSON (no lista) lanza ParseError."""
        with pytest.raises(ParseError, match="Se esperaba una lista"):
            parse_conversation("42")
