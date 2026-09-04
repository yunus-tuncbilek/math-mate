"""RAG embeddings are per-class: retrieval never crosses class boundaries.

These exercise the real sentence-transformer model, so they're a touch slow on
first run (model load), but they pin the behavior that motivated storing
embeddings per class in the first place.
"""
import app_utils
from models import Class, Resource, ResourceChunk, User


def _class_with_resource(text, name="Algebra"):
    teacher = User(email=f"t-{name}@ex.com", password_hash="x", role="teacher", name="T")
    from extensions import db

    db.session.add(teacher)
    db.session.flush()
    klass = Class(teacher_id=teacher.id, name=name, invite_code=f"code-{name}")
    db.session.add(klass)
    db.session.flush()
    resource = Resource(class_id=klass.id, title=f"{name} notes", text_content=text)
    db.session.add(resource)
    db.session.commit()
    app_utils.index_resource(resource)
    return klass, resource


def test_index_resource_creates_chunks(app):
    _klass, resource = _class_with_resource("Photosynthesis converts light to sugar.")
    chunks = ResourceChunk.query.filter_by(resource_id=resource.id).all()
    assert len(chunks) >= 1
    assert all(c.embedding for c in chunks)


def test_index_resource_no_text_no_chunks(app):
    from extensions import db

    teacher = User(email="t@ex.com", password_hash="x", role="teacher", name="T")
    db.session.add(teacher)
    db.session.flush()
    klass = Class(teacher_id=teacher.id, name="Empty", invite_code="empty")
    db.session.add(klass)
    db.session.flush()
    resource = Resource(class_id=klass.id, title="File only", file_path="x.pdf")
    db.session.add(resource)
    db.session.commit()

    assert app_utils.index_resource(resource) == 0
    assert ResourceChunk.query.filter_by(resource_id=resource.id).count() == 0


def test_retrieval_is_scoped_to_class(app):
    algebra, algebra_res = _class_with_resource(
        "A quadratic equation has the form a x squared plus b x plus c.", "Algebra"
    )
    biology, bio_res = _class_with_resource(
        "Mitochondria are the powerhouse of the cell.", "Biology"
    )

    # A biology question, but scoped to the algebra class, must NOT return the
    # biology chunk — that's the whole point of per-class storage.
    hit, source = app_utils.closest_lecture_chunk("what is a cell organelle", [algebra.id])
    assert "Mitochondria" not in hit
    assert "quadratic" in hit.lower()
    assert source == {"id": algebra_res.id, "title": algebra_res.title}

    # Same question scoped to biology returns the biology chunk.
    hit_bio, source_bio = app_utils.closest_lecture_chunk(
        "what is a cell organelle", [biology.id]
    )
    assert "Mitochondria" in hit_bio
    assert source_bio == {"id": bio_res.id, "title": bio_res.title}


def test_retrieval_empty_when_no_classes(app):
    assert app_utils.closest_lecture_chunk("anything", []) == ("", None)


def test_deleting_resource_removes_its_chunks(app):
    from extensions import db

    _klass, resource = _class_with_resource("A chunk that should vanish on delete.")
    rid = resource.id
    assert ResourceChunk.query.filter_by(resource_id=rid).count() >= 1

    db.session.delete(resource)
    db.session.commit()

    assert ResourceChunk.query.filter_by(resource_id=rid).count() == 0
