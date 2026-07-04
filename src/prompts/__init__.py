"""Cargar todas las plantillas de prompt ``.txt`` al inicio.

Los prompts se almacenan como archivos de texto plano para que puedan
revisarse y editarse sin tocar código Python.
"""

from __future__ import annotations

import pathlib
from functools import cache

_PROMPT_DIR = pathlib.Path(__file__).resolve().parent


@cache
def load_prompts() -> dict[str, str]:
    """Escanea ``src/prompts/`` en busca de archivos ``.txt`` y retorna ``{stem: contenido}``.

    Los resultados se cachean para que llamadas múltiples (ej. reruns de
    Streamlit) eviten releer los archivos del disco.

    Returns
    -------
    dict[str, str]
        Mapeo del nombre del archivo (ej. ``"sentiment"``) a su contenido.
    """
    prompts: dict[str, str] = {}
    for path in sorted(_PROMPT_DIR.glob("*.txt")):
        prompts[path.stem] = path.read_text(encoding="utf-8")
    return prompts
