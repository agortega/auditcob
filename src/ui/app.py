"""Interfaz web Streamlit para el pipeline de AuditCob.

Provee:
- Área de texto para entrada JSON
- Toggle de modo simulado para pruebas offline
- Barras de progreso por etapa (5 etapas)
- Salida estructurada del reporte en pestañas
"""

from __future__ import annotations

import json
import time
from typing import Any

import streamlit as st

from src.main import STAGES, run_pipeline
from src.models import AuditReport
from src.parser import ParseError

# ── Configuración de página ──────────────────────────────────────────────

st.set_page_config(
    page_title="AuditCob — Auditor de Gestión de Cobranzas",
    page_icon="🤖",
    layout="wide",
)

# ── Inicialización del estado de sesión ───────────────────────────────────

if "report" not in st.session_state:
    st.session_state.report = None
if "error" not in st.session_state:
    st.session_state.error = ""
if "pipeline_done" not in st.session_state:
    st.session_state.pipeline_done = False

# ── Título ────────────────────────────────────────────────────────────────

st.markdown(
    "# 🤖 AuditCob — Auditor de Gestión de Cobranzas\n\n"
    "Ingrese una conversación en formato JSON y ejecute el pipeline "
    "de 5 etapas para obtener un análisis completo."
)

# ── Área de entrada ───────────────────────────────────────────────────────

col_input, col_config = st.columns([3, 1])

with col_input:
    json_input = st.text_area(
        "Conversación (JSON)",
        value=(
            '[{"agente": "Señor, debe pagar hoy", '
            '"cliente": "disculpeme pero no puedo pagar"}, '
            '{"agente": "Lo siento pero no somos caridad", '
            '"cliente": "..."}]'
        ),
        placeholder='[{"agente": "...", "cliente": "..."}]',
        height=180,
    )

with col_config:
    mock_mode = st.checkbox("Modo mock (sin Ollama)", value=True)
    analyze_btn = st.button("🔍 Analizar", type="primary", use_container_width=True)

# ── Ejecución del pipeline ────────────────────────────────────────────────

if analyze_btn:
    st.session_state.report = None
    st.session_state.error = ""
    st.session_state.pipeline_done = False

    if not json_input.strip():
        st.session_state.error = "Error: Ingrese un JSON de conversación."
    else:
        # Validar JSON antes de tocar el pipeline
        try:
            json.loads(json_input)
        except json.JSONDecodeError as exc:
            st.session_state.error = f"Error: JSON inválido — {exc}"

        if not st.session_state.error:
            progress_bar = st.progress(0.0, text="Iniciando…")
            status_text = st.empty()

            try:
                # ── Crear ayudantes ─────────────────────────────────
                from src.prompts import load_prompts

                prompts = load_prompts()

                from src.analyzer import OllamaClient
                from dotenv import load_dotenv
                import os

                load_dotenv()
                client = OllamaClient(
                    host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                    model=os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud"),
                    mock=mock_mode,
                )

                # ── Parsear ─────────────────────────────────────────
                from src.models import AuditContext, Conversation
                from src.parser import parse_conversation

                progress_bar.progress(0.05, text="Validando JSON…")
                time.sleep(0.2)

                conversation: Conversation = parse_conversation(json_input)
                ctx = AuditContext(conversation=conversation)
                progress_bar.progress(0.1, text="Parseando conversación…")
                time.sleep(0.2)

                # ── Ejecutar etapas con progreso ─────────────────────
                total_steps = len(STAGES)
                step_size = 0.80 / total_steps
                current = 0.1

                stage_labels = {
                    "sentiment": "1/5 — Analizando sentimiento",
                    "bad_practices": "2/5 — Detectando malas prácticas",
                    "rating": "3/5 — Calculando calificación",
                    "summary": "4/5 — Generando resumen",
                    "feedback": "5/5 — Creando retroalimentación",
                }

                for name, builder in STAGES:
                    current += step_size
                    label = stage_labels.get(name, name)
                    progress_bar.progress(current, text=label)

                    stage_fn = builder(prompts)
                    ctx = stage_fn(ctx, client)

                # ── Construir reporte ──────────────────────────────
                progress_bar.progress(0.95, text="Generando reporte…")
                report = AuditReport(
                    total_turns=len(ctx.conversation.turns),
                    sentiment=ctx.sentiment,
                    bad_practices=ctx.bad_practices,
                    rating=ctx.rating,
                    summary=ctx.summary,
                )

                progress_bar.progress(1.0, text="¡Completado!")
                time.sleep(0.3)
                progress_bar.empty()

                st.session_state.report = report
                st.session_state.pipeline_done = True

            except ParseError as exc:
                st.session_state.error = f"Error de parseo: {exc}"
            except RuntimeError as exc:
                st.session_state.error = f"Error del pipeline: {exc}"
            except Exception as exc:  # noqa: BLE001
                st.session_state.error = f"Error inesperado: {exc}"

# ── Mostrar error ─────────────────────────────────────────────────────────

if st.session_state.error:
    st.error(st.session_state.error)

# ── Mostrar resultados ────────────────────────────────────────────────────

if st.session_state.pipeline_done and st.session_state.report:
    report: AuditReport = st.session_state.report

    st.markdown("## Resultados")

    tab_sentiment, tab_bad, tab_rating, tab_summary, tab_feedback = st.tabs(
        ["😊 Sentimiento", "⚠️ Malas Prácticas", "⭐ Calificación", "📋 Resumen", "💡 Feedback"]
    )

    with tab_sentiment:
        s = report.sentiment
        if s:
            st.markdown(f"**Agente:** {s.agent_sentiment}")
            st.markdown(f"**Cliente:** {s.client_sentiment}")
            st.markdown("**Evolución:**")
            for e in s.evolution:
                st.markdown(f"- {e}")
        else:
            st.info("*Sin datos*")

    with tab_bad:
        bp = report.bad_practices
        if bp:
            for i, p in enumerate(bp, 1):
                with st.container(border=True):
                    st.markdown(f"**{i}. {p.practice}** — severidad: `{p.severity}`")
                    st.markdown(f"- **Cita:** \"{p.citation}\"")
                    st.markdown(f"- **Recomendación:** {p.recommendation}")
        else:
            st.success("No se detectaron malas prácticas.")

    with tab_rating:
        r = report.rating
        if r:
            score = r.score
            if score >= 80:
                st.metric("Puntaje", f"{score}/100", delta_color="normal")
            elif score >= 50:
                st.metric("Puntaje", f"{score}/100", delta_color="inverse")
            else:
                st.metric("Puntaje", f"{score}/100", delta_color="off")
            st.markdown(f"**Nivel:** {r.level}")
            st.markdown(f"**Explicación:** {r.explanation}")
        else:
            st.info("*Sin datos*")

    with tab_summary:
        sm = report.summary
        if sm and sm.summary:
            st.markdown(sm.summary)
        else:
            st.info("*Sin datos*")

    with tab_feedback:
        sm = report.summary
        if sm and sm.opportunities:
            for o in sm.opportunities:
                st.markdown(f"- {o}")
        else:
            st.info("*Sin oportunidades de mejora*")

# ── Footer ───────────────────────────────────────────────────────────────

st.divider()
st.caption(
    "**AuditCob** — Proyecto del Semillero de IA 2026. "
    "Usa Ollama + Gemma 4 para análisis de conversaciones de cobranza."
)
