"""RLHF-lite: learn from student feedback without any model training.

The AI tutor cannot be fine-tuned here, so instead we close the loop the cheap
way: every time a student rates the tutor's help as *unhelpful* we keep that
exchange as a "lesson". Before answering a new question we retrieve the lessons
most similar to it and inject them into the prompt's *Error database* section,
telling the model to avoid repeating those mistakes.

This is the "human feedback -> better next response" idea of RLHF, minus the
reinforcement-learning machinery — hence *RLHF-lite*.

Rating convention (see ``templates/chat.html`` / the ``/feedback`` route):
    5 = 👍 helpful, 1 = 👎 not helpful. Anything <= ``NEGATIVE_MAX`` counts as
    negative and becomes a lesson.
"""
from models import Feedback, ChatSession

# A rating at or below this value is treated as negative feedback.
NEGATIVE_MAX = 2

# How many candidate lessons to pull from the DB before ranking by relevance.
_CANDIDATE_POOL = 50


def _lesson_from_session(chat_session, comment):
    """Extract a compact lesson (question / bad answer / comment) from a session.

    Uses the last student question and the assistant reply that followed it —
    that reply is what the student was rating.
    """
    last_question = None
    bad_answer = None
    for msg in chat_session.messages:  # ordered oldest -> newest
        if msg.role == "user":
            last_question = msg.content
        elif msg.role == "assistant":
            bad_answer = msg.content
    if not last_question and not bad_answer:
        return None
    return {
        "question": last_question or "",
        "bad_answer": bad_answer or "",
        "comment": comment or "",
    }


def _collect_negative_lessons():
    """Most-recent-first list of lessons drawn from negatively rated sessions."""
    rows = (
        Feedback.query.filter(
            Feedback.rating.isnot(None), Feedback.rating <= NEGATIVE_MAX
        )
        .order_by(Feedback.created_at.desc())
        .limit(_CANDIDATE_POOL)
        .all()
    )
    lessons = []
    for fb in rows:
        session = fb.session or ChatSession.query.get(fb.chat_session_id)
        if session is None:
            continue
        lesson = _lesson_from_session(session, fb.comment)
        if lesson:
            lessons.append(lesson)
    return lessons


def _rank_by_relevance(question, lessons, limit):
    """Return the ``limit`` lessons most similar to ``question``.

    Falls back to recency (the input order) if the embedding model is
    unavailable or anything goes wrong — the feature must never break a reply.
    """
    if len(lessons) <= limit:
        return lessons
    try:
        from rag import rag_utils

        lesson_questions = [l["question"] or l["bad_answer"] for l in lessons]
        embeddings = rag_utils.get_embeddings(lesson_questions)
        _, _, indices, _, _ = rag_utils.retrieve_closest_chunk(
            question, lesson_questions, embeddings, top_k=limit
        )
        return [lessons[int(i)] for i in indices]
    except Exception:
        # Embedding stack missing/slow/failed — degrade gracefully to recency.
        return lessons[:limit]


def _format(lessons):
    parts = [
        "Past cases where a student rated the tutor's help as UNHELPFUL. "
        "Study them and do NOT repeat these mistakes:"
    ]
    for i, lesson in enumerate(lessons, 1):
        block = [f"{i}. Student asked: {lesson['question']!r}"]
        if lesson["bad_answer"]:
            block.append(f"   The unhelpful reply was: {lesson['bad_answer']!r}")
        if lesson["comment"]:
            block.append(f"   Student said what was wrong: {lesson['comment']!r}")
        parts.append("\n".join(block))
    return "\n".join(parts)


def build_error_database(question, limit=3):
    """Build the *Error database* prompt block for a given question.

    Returns an empty string when there is nothing to learn from yet, so the
    common (no-negative-feedback) case adds zero prompt overhead and skips the
    embedding model entirely.
    """
    if not question:
        return ""
    lessons = _collect_negative_lessons()
    if not lessons:
        return ""
    lessons = _rank_by_relevance(question, lessons, limit)
    return _format(lessons)
