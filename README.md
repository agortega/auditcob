# AuditCob — Auditor de Gestión de Cobranzas

> Proyecto del Semillero de IA 2026

**AuditCob** es un agente de IA que audita automáticamente conversaciones de
gestores de cobranzas. Recibe un JSON con el diálogo entre asesor y cliente,
analiza la atención brindada, identifica malas prácticas, califica la gestión
y genera retroalimentación para mejorar el desempeño del asesor.

## Arquitectura

```
                    ┌──────────────────────────────────────────────┐
                    │               Streamlit UI                   │
                    │   Input JSON  →  5 barras de progreso   →   │
                    │                Reporte estructurado          │
                    └──────────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────▼───────────────────────┐
                    │              Pipeline Orchestrator           │
                    │         src/main.py — run_pipeline()         │
                    └──────────────────────┬───────────────────────┘
                                           │
        ┌────────────┬────────────┬────────┼────────┬────────────┬───────────┐
        ▼            ▼            ▼        ▼        ▼            ▼           ▼
   ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────┐ ┌────────┐ ┌────────┐ ┌──────────┐
   │  Parser  │ │ Stage 1  │ │Stage 2 │ │Stage3│ │Stage 4 │ │Stage 5 │ │  Mock    │
   │          │ │Sentiment │ │  Bad    │ │Rating│ │Summary │ │Feedback│ │ (opcional)│
    │JSON→Conv │ │analysis  │ │Practices│ │0-100 │ │        │ │        │ │          │
   └──────────┘ └──────────┘ └────────┘ └──────┘ └────────┘ └────────┘ └──────────┘
        │             │            │         │         │          │            │
        └─────────────┴────────────┴─────────┴─────────┴──────────┴────────────┘
                                      │
                              ┌───────▼────────┐
                              │  AuditContext   │
                              │  (acumulador    │
                              │   tipado)       │
                              └───────┬────────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │  AuditReport   │
                              │   (reporte     │
                              │    final)      │
                              └───────────────┘
```

## Pipeline (5 etapas)

| Etapa | Archivo | Descripción |
|-------|---------|-------------|
| 1. Sentimiento | `src/stages/sentiment.py` | Analiza sentimiento del agente y cliente por turno + evolución |
| 2. Malas Prácticas | `src/stages/bad_practices.py` | Detecta amenazas, presión, rudeza o lenguaje no profesional |
| 3. Calificación | `src/stages/rating.py` | Puntúa la gestión 0–100 con nivel y explicación |
| 4. Resumen | `src/stages/summary.py` | Genera resumen ejecutivo de la conversación |
| 5. Feedback | `src/stages/feedback.py` | Genera oportunidades de mejora para el asesor |

## Stack Tecnológico / Herramientas

### Herramientas de desarrollo y ejecución
| Herramienta | Versión | Propósito |
|---|---|---|
| **Python** | 3.11.3 | Lenguaje base |
| **Ollama** | v0.30.10 | Motor de modelos de lenguaje local/cloud |
| **gemma4:31b-cloud** | — | Modelo de lenguaje para análisis de conversaciones |
| **Streamlit** | ≥1.28 | Interfaz web interactiva |
| **Pydantic** | ≥2.0 | Esquemas tipados y validación de datos |
| **httpx** | ≥0.24 | Cliente HTTP para la API de Ollama |
| **python-dotenv** | ≥1.0 | Configuración vía variables de entorno |

### Herramientas de calidad y testing
| Herramienta | Propósito |
|---|---|
| **pytest** | Framework de tests unitarios |
| **pytest-cov** | Medición de cobertura de código |
| **unittest.mock** | Simulación de llamadas HTTP para tests |

### Pipeline de análisis (5 herramientas del agente)

El agente auditor expone 5 herramientas que se ejecutan en secuencia sobre la conversación:

| # | Herramienta | Decorador conceptual | Descripción |
|---|---|---|---|
| 1 | **`analizar_sentimiento`** | `@tool` | Clasifica sentimiento del agente y cliente por turno + evolución |
| 2 | **`detectar_malas_practicas`** | `@tool` | Identifica amenazas, presión, rudeza o lenguaje no profesional |
| 3 | **`calificar_gestion`** | `@tool` | Asigna puntaje 0–100 con nivel y explicación |
| 4 | **`resumir_conversacion`** | `@tool` | Genera resumen ejecutivo de la conversación |
| 5 | **`generar_retroalimentacion`** | `@tool` | Crea oportunidades de mejora para el asesor |

> Cada tool usa un prompt específico (archivos `.txt` en `src/prompts/`) y devuelve un modelo Pydantic distinto. El orquestador las ejecuta en orden fijo — no hay un loop de agente decidiendo dinámicamente qué tool llamar. Esto mantiene el análisis determinista y fácil de testear.

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/tuusuario/auditcob.git
cd auditcob

# 2. Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Instalar el paquete en modo desarrollo
pip install -e .

# 5. Configurar variables de entorno
cp .env.example .env
# Editar .env si es necesario (los defaults funcionan con Ollama local)
```

## Requisitos

- **Ollama** corriendo (local o cloud):
  ```bash
  ollama pull gemma4:31b-cloud
  ollama serve
  ```
- **Python 3.11+** con pip

## Uso

### Interfaz Web (Streamlit)

```bash
streamlit run src/ui/app.py
```

> Si ves el error `ModuleNotFoundError: No module named 'src'`, asegurate de haber ejecutado `pip install -e .` desde la raíz del proyecto (paso 4 de Instalación). Eso registra el paquete en el entorno virtual y resuelve los imports.

Abrir http://localhost:8501 en el navegador.

1. Ingresar el JSON de la conversación en el área de texto.
2. Opcional: activar **Modo mock** para probar sin Ollama.
3. Hacer clic en **Analizar**.
4. Observar el progreso etapa por etapa.
5. Revisar los resultados en las pestañas.

### Línea de comandos

```bash
# Modo mock (sin Ollama)
python -m src.main --mock

# Modo real (requiere Ollama)
python -m src.main '[
  {"agente": "Señor, debe pagar hoy", "cliente": "disculpeme pero no puedo pagar"},
  {"agente": "Lo siento pero no somos caridad", "cliente": "..."}
]'
```

## Formato del JSON de entrada

```json
[
  {"agente": "texto del asesor", "cliente": "texto del cliente"},
  {"agente": "más texto", "cliente": "más texto"}
]
```

- Lista de objetos con exactamente dos claves: `agente` y `cliente`.
- Ambos campos deben ser textos no vacíos.

## Ejemplo de Salida

```json
{
  "total_turns": 2,
  "sentiment": {
    "agent_sentiment": "profesional",
    "client_sentiment": "resistente",
    "evolution": [
      "El agente inicia cordialmente",
      "El cliente se muestra evasivo",
      "Se alcanza un acuerdo parcial"
    ]
  },
  "bad_practices": [
    {
      "practice": "Presión indebida",
      "severity": "media",
      "citation": "Lo siento pero no somos caridad",
      "recommendation": "Usar lenguaje neutral"
    }
  ],
  "rating": {
    "score": 65,
    "level": "regular",
    "explanation": "Tono profesional pero con presión innecesaria"
  },
  "summary": {
    "summary": "Resumen ejecutivo de la conversación...",
    "opportunities": [
      "Ofrecer planes de pago desde el primer contacto",
      "Mantener un tono empático"
    ]
  }
}
```

## Ejemplos de Respuestas del Agente

### Entrada (JSON de conversación)

```json
[
  {"agente": "Señor, debe pagar hoy", "cliente": "disculpeme pero no puedo pagar"},
  {"agente": "Lo siento pero no somos caridad", "cliente": "..."}
]
```

### Salida esperada — Vista por etapas

**Etapa 1 — Sentimiento:**
- Agente: `profesional`
- Cliente: `resistente`
- Evolución: el agente inicia cordialmente → el cliente se muestra evasivo → cierre con acuerdo parcial

**Etapa 2 — Malas prácticas detectadas:**
| Práctica | Severidad | Cita | Recomendación |
|---|---|---|---|
| Presión indebida | media | "Lo siento pero no somos caridad" | Usar lenguaje neutral y evitar amenazas implícitas |

**Etapa 3 — Calificación:**
- Puntaje: **65/100** — Nivel: `regular`
- Explicación: la conversación se mantuvo profesional pero se detectaron momentos de presión

**Etapa 4 — Resumen ejecutivo:**
> El agente contactó al cliente para gestionar el pago de una deuda. El cliente mostró resistencia inicial pero se acordó una visita para revisar alternativas.

**Etapa 5 — Oportunidades de mejora:**
- Ofrecer planes de pago desde el primer contacto
- Mantener un tono empático ante la resistencia del cliente
- Evitar frases que puedan interpretarse como presión

## Tests

```bash
# Ejecutar todos los tests
pytest -v

# Con cobertura
pytest --cov=src tests/
```

## Estructura del Proyecto

```
.
├── LICENSE               # Licencia MIT
├── pyproject.toml        # Configuración del paquete
├── .env.example          # Variables de entorno de ejemplo
├── .gitignore            # Exclusiones
├── README.md             # Este archivo
├── requirements.txt      # Dependencias
├── src/
│   ├── __init__.py
│   ├── main.py           # Orquestador del pipeline
│   ├── models.py         # Esquemas Pydantic
│   ├── parser.py         # Validador JSON de entrada
│   ├── analyzer.py       # Cliente Ollama con retry y mock
│   ├── prompts/
│   │   ├── __init__.py   # Cargador de prompts
│   │   ├── sentiment.txt
│   │   ├── bad_practices.txt
│   │   ├── rating.txt
│   │   ├── summary.txt
│   │   └── feedback.txt
│   ├── stages/
│   │   ├── __init__.py   # Type alias StageFn
│   │   ├── sentiment.py
│   │   ├── bad_practices.py
│   │   ├── rating.py
│   │   ├── summary.py
│   │   └── feedback.py
│   └── ui/
│       ├── __init__.py
│       └── app.py        # Interfaz Streamlit
└── tests/
    ├── __init__.py
    ├── conftest.py       # Fixtures
    ├── test_parser.py    # Tests del parser
    ├── test_analyzer.py  # Tests del cliente Ollama
    └── test_stages.py    # Tests de las 5 etapas
```

## Criterios de Éxito

- [x] Parser valida todos los formatos de conversación
- [x] Cada etapa produce salida estructurada independientemente
- [x] Pipeline completo funciona end-to-end vía Streamlit
- [x] Streamlit muestra progreso por etapa con resultado estructurado
- [x] pytest pasa con ≥80% de cobertura en módulos core
- [x] README con setup, diagrama de arquitectura y ejemplos
- [x] Repositorio público, sin credenciales ni datos reales

## Seguridad

- Las credenciales de Ollama se configuran vía `.env` (excluido del repo).

---

_Proyecto del Semillero de IA — 2026-
