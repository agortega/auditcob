"""Parser y validador de conversaciones JSON.

Transforma el JSON crudo de entrada (``list[dict[str, str]]``) en un
modelo :class:`Conversation` tipado. Rechaza esquemas inválidos con
errores claros.
"""

from __future__ import annotations

import json
from typing import Any

from src.models import Conversation, Turn


class ParseError(Exception):
    """Se lanza cuando la entrada no se puede parsear como conversación válida."""


def parse_conversation(raw: str) -> Conversation:
    """Parsear y validar una conversación en formato JSON.

    Parameters
    ----------
    raw:
        Cadena JSON que representa un ``list[dict[str, str]]`` con claves
        ``"agente"`` y ``"cliente"``.

    Returns
    -------
    Conversation
        Un modelo de conversación validado.

    Raises
    ------
    ParseError
        Si el JSON está mal formado, no es una lista, los ítems no son
        diccionarios, o faltan claves requeridas / están en blanco.
    """
    try:
        datos: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ParseError(f"JSON inválido: {exc}") from exc

    if not isinstance(datos, list):
        raise ParseError(
            "Se esperaba una lista de objetos, pero se recibió "
            f"{type(datos).__name__}."
        )

    turnos: list[Turn] = []
    for i, elemento in enumerate(datos):
        if not isinstance(elemento, dict):
            raise ParseError(
                f"El elemento [{i}] no es un objeto: "
                f"se recibió {type(elemento).__name__}."
            )

        agente = elemento.get("agente", "")
        cliente = elemento.get("cliente", "")

        errores: list[str] = []
        if "agente" not in elemento:
            errores.append("Falta la clave 'agente'")
        elif not isinstance(agente, str) or not agente.strip():
            errores.append("'agente' debe ser un texto no vacío")

        if "cliente" not in elemento:
            errores.append("Falta la clave 'cliente'")
        elif not isinstance(cliente, str) or not cliente.strip():
            errores.append("'cliente' debe ser un texto no vacío")

        if errores:
            raise ParseError(f"Elemento [{i}]: {'; '.join(errores)}.")

        turnos.append(Turn(agente=agente.strip(), cliente=cliente.strip()))

    return Conversation(turns=turnos)
