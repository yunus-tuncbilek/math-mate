# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Math-Mate is a Flask web app that is both a per-class content/homework manager and an AI homework tutor for teachers and students. It is server-rendered (Jinja2 + a little vanilla JS), backed by SQLAlchemy, and uses Together AI for generation plus a local `sentence-transformers` RAG/RLHF-lite retrieval pipeline.

## Commands

```bash
# Setup
pip install -r requirements.txt
cp .env.example .env        # then set `secret_key` and TOGETHER_API_KEY
flask db upgrade            # apply Alembic migrations (creates tables)

# Run (dev)
python app.py               # debug server on the Flask default port

# Tests
pytest -q                   # full suite
pytest tests/test_rag.py    # a single file
pytest tests/test_smoke.py::test_signup_then_login_flow   # a single test

# DB migrations (after changing models.py)
flask db migrate -m "message"
flask db upgrade
```

`flask` CLI commands need `FLASK_APP=app.py` (the Dockerfile sets it; set it locally if unset).

## Environment & config

`config.py` loads `.env` at import time. Required: `secret_key` (app raises on boot without it). `DATABASE_URL` is optional and defaults to a local SQLite file at `data/mathmate.db`; set it to a Postgres/Supabase URL for a zero-code-change swap (uncomment `psycopg2-binary` in requirements). `TOGETHER_API_KEY` is only needed when an actual LLM call is made.

## Architecture

Request flow: `app.py` (routes) → `app_utils.py` (all data access) → `models.py` (SQLAlchemy) via the shared extension instances in `extensions.py`. Keep new DB reads/writes in `app_utils.py` rather than inline in routes.

- **`extensions.py`** holds `db`, `migrate`, `login_manager` as bare instances so `app.py`, `models.py`, and the Alembic env can import them without circular imports. They are `.init_app(app)`-ed in `app.py`.
- **Role-based access** is enforced server-side on every protected route via the `@teacher_required` / `@student_required` decorators in `app.py` (both wrap `@login_required`). Ownership is re-checked in handlers (e.g. a teacher can only touch a class/assignment/resource whose `class.teacher_id` matches them). Scoping helpers in `app_utils.py` (`class_ids_for_student/teacher`, `assignments_for_user`, `resources_for_user`, `chat_sessions_visible_to`) filter every listing by role.
- **Data model** (`models.py`): `User` (role = "student"|"teacher") → teacher owns `Class`es (each with a unique `invite_code`); students join via `ClassStudent` (many-to-many). A `Class` has `Assignment`s and `Resource`s. Chat is `ChatSession` → `ChatMessage` (+ one `Feedback` row). RAG lives in `ResourceChunk` (chunk text + float32 embedding blob).

### The `guidance_note` privacy invariant

`Assignment.guidance_note` is the teacher's **private** instruction to the AI and must never reach a student. This is a load-bearing security property (documented in the `models.py` module docstring and covered by tests):
- Serialize student-facing assignments with `Assignment.public_dict()` (or `to_dict(include_guidance=False)`, the default). Only pass `include_guidance=True` in teacher-authenticated views.
- In the chat path, `guidance` is injected into the prompt only and is never streamed to the client.

### AI chat & streaming

`/chat/stream` (in `app.py`) is the primary path: the browser calls it via `fetch` (`static/chat.js`) and the reply streams token-by-token as **Server-Sent Events**. All DB work (history, RAG retrieval, RLHF error-db, saving the student message) happens up front in request scope; the generator only emits tokens and then persists the assistant reply once complete. `respond.py` owns `build_prompt()` (single source of truth for the tutor prompt) and `stream_ai_response()` → `stream_llm()`, which lazily creates the Together client (`MODEL = "openai/gpt-oss-20b"`).

**Context scoping** is the key correctness rule: when a chat is tied to an assignment, both the homework context and RAG retrieval are scoped to that assignment's `class_id`; otherwise they fall back to all of the student's enrolled classes. This keeps another class's material out of the prompt.

### RAG (per-class, in `rag/rag_utils.py` + `app_utils.py`)

Resource `text_content` (not PDF binaries — there is no PDF text extraction) is chunked and embedded with `all-MiniLM-L6-v2`, stored as `ResourceChunk` rows with the embedding as raw float32 bytes (`serialize_embedding`/`deserialize_embedding`). `app_utils.index_resource()` (re)builds a resource's chunks; `closest_lecture_chunk(question, class_ids)` retrieves the single best chunk via scikit-learn cosine similarity, **filtered to the given classes** so retrieval never crosses class boundaries (the invariant `tests/test_rag.py` pins). Deleting a `Resource` cascades to its chunks.

### RLHF-lite (`rlhf.py`)

No model training. Sessions rated `<= NEGATIVE_MAX` (1 = 👎) become "lessons." Before answering, `build_error_database(question)` pulls recent negative lessons, ranks the most semantically similar (same embedding stack, **degrading gracefully to recency** on any failure — it must never break a reply), and injects them into the prompt's *Error database* block as "what not to do." Returns `""` when there's no negative feedback, so the common case adds zero overhead and skips the embedding model.

### Lazy loading

Heavy ML deps (`torch`/`sentence-transformers`) and the Together client are imported **inside functions**, not at module top level, to keep app boot and the Flask CLI fast. Preserve this pattern — import `rag.rag_utils` and `together` locally where used.

## Testing notes

`tests/conftest.py` sets `secret_key` and points `DATABASE_URL` at a throwaway temp SQLite **file** (not `:memory:`, so the connection pool shares one DB) *before* importing `app`, since `config.py` reads env at import time. Fixtures `app` and `client` create/drop tables per test. `tests/test_rag.py` runs the real embedding model (slow on first run, loads weights once).

## Deployment

Docker image (`Dockerfile`, Python 3.9) runs `flask db upgrade && gunicorn ... app:app` at container start (port 7860). CI (`.github/workflows/tests.yml`) runs `pytest -q` on every push/PR to `main`; on `main` only, after tests pass, it force-pushes to a Hugging Face Space (`HF_TOKEN` secret).
