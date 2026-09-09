---
title: "Math-Mate"
emoji: "👀"
colorFrom: "pink"
colorTo: "indigo"
sdk: "docker"
pinned: false
license: "apache-2.0"
---

# Math-Mate

[![Tests](https://github.com/yunus-tuncbilek/math-mate/actions/workflows/tests.yml/badge.svg)](https://github.com/yunus-tuncbilek/math-mate/actions/workflows/tests.yml)

Math-Mate is a comprehensive web-based platform that serves as both a content
management system and an AI-powered tutoring assistant for homework assignments.
Designed for teachers, professors, and students, Math-Mate streamlines the
homework process and enhances learning through intelligent, context-aware support.

## Features

### Teaching & learning
- **Accounts & Roles:** Teachers and students sign up for their own accounts,
  with role-aware dashboards and access control (Flask-Login sessions plus
  `@teacher_required` / `@student_required` route guards) throughout the app.
- **Classes & Enrollment:** Teachers create classes that come with a unique
  invite code. Students join with that code, and teachers can also invite an
  existing student directly by email. Assignments and resources are organized
  per class through a proper many-to-many enrollment model.
- **Homework & Resources:** Educators upload and manage homework assignments and
  lecture resources per class. Resources can be uploaded as **PDFs** (rendered
  in-browser) or entered as **plain text**.
- **Student Homework Portal:** Students view and access assigned homework through
  a responsive, multi-page dashboard with a collapsible navigation menu.
- **LaTeX / Math rendering:** Assignments and AI replies render mathematical
  notation with **MathJax**, so the tutor can answer in real math syntax.

### AI tutor
- **Streaming AI Tutor:** An integrated AI tutor helps students with their
  homework, offering explanations, hints, and step-by-step guidance. Replies are
  streamed **token-by-token over Server-Sent Events (SSE)**, rendered live in the
  browser via `fetch`, and gracefully fall back to a plain form POST when
  JavaScript is unavailable. Powered by the **Together AI** API
  (`openai/gpt-oss-20b`).
- **RAG (Retrieval-Augmented Generation):** Lecture resources are chunked and
  embedded with **`sentence-transformers` (all-MiniLM-L6-v2)**; the most relevant
  chunk for each question is retrieved via **scikit-learn cosine similarity** and
  injected into the prompt, along with a link back to the source resource.
  Embeddings are **built per class** and stored as float32 blobs in the database,
  so retrieval never crosses class boundaries and a student never sees another
  class's material.
- **Private Teacher Guidance:** Teachers can attach a private `guidance_note` to
  an assignment that steers the tutor's behaviour. It is injected into the prompt
  as a non-disclosable directive and is **never** serialized into any
  student-facing view (enforced by a `public_dict()` guard and covered by tests).
- **Context scoping:** When a chat is tied to an assignment, both the homework
  context and the RAG retrieval are scoped to that assignment's class, so the AI
  only ever reasons over the relevant material.

### Feedback loop
- **Student Feedback System:** After receiving AI assistance, students rate the
  help (👍 / 👎) and can leave a comment.
- **RLHF-lite Improvement:** Negatively-rated exchanges become "lessons." Before
  answering a new question, the lessons most **semantically similar** to it
  (ranked with the same embedding stack, degrading gracefully to recency) are
  injected into the prompt's *Error database* section, telling the model what to
  avoid — the human-feedback → better-response idea of RLHF, without the
  reinforcement-learning machinery.
- **Teacher Review Tools:** Teachers gain insight into student progress and
  common challenges by reviewing chat history and feedback.

## Technology

- **Backend:** Python + **Flask**, served in production by **Gunicorn**.
- **Frontend:** Server-rendered **Jinja2** templates (Flask's templating engine)
  with a shared `base.html` layout and per-page templates, styled with plain CSS
  (responsive, with a collapsible hamburger nav). No SPA framework — a small
  amount of **vanilla JavaScript** (`static/chat.js`) consumes the Server-Sent
  Events stream and renders the tutor's reply live, with **MathJax** rendering
  LaTeX math in assignments and AI replies.
- **Database:** **SQLAlchemy** ORM models with **Flask-Migrate (Alembic)**
  migrations (replacing the earlier JSON-file storage). Defaults to a local
  **SQLite** file for zero-config local dev; point `DATABASE_URL` at
  **Postgres/Supabase** (via `psycopg2`) for a one-line production swap.
- **AI / ML:** Together AI for generation; `sentence-transformers`, `scikit-learn`,
  and `numpy` for the RAG and RLHF-lite retrieval pipeline. Heavy ML dependencies
  and the Together client are **loaded lazily** so app boot and the Flask CLI stay
  fast.
- **Testing:** **pytest** suite (`tests/`) with smoke tests (boot, page render,
  auth guards, signup/login flow) and RAG tests that pin per-class embedding
  isolation.
- **CI/CD:** **GitHub Actions** (`.github/workflows/tests.yml`) runs the pytest
  suite on every push and PR to `main`, then — only after tests pass, only on
  `main` — auto-deploys by pushing to a **Hugging Face Space**.
- **Deployment:** **Docker** image that applies migrations and serves via
  Gunicorn on Hugging Face Spaces. The Dockerfile uses layer caching to avoid
  re-installing packages with every build, leading to faster rebuilds. 

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd math-mate
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment:** copy `.env.example` to `.env` and set a
   `secret_key`. Optionally set `DATABASE_URL` to use Postgres/Supabase instead
   of the default SQLite file.
4. **Set up the database:**
   ```bash
   flask db upgrade   # create the tables from the Alembic migrations
   ```
5. **Add your AI key:** get an API key from [Together AI](https://www.together.ai)
   and store it in `.env` as `TOGETHER_API_KEY`.
6. **Run the web application:**
   ```bash
   python app.py
   ```

## Running the tests

```bash
pytest -q
```
