"""add resource_chunks table for per-class RAG embeddings

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'resource_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('embedding', sa.LargeBinary(), nullable=False),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('resource_chunks', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_resource_chunks_resource_id'),
            ['resource_id'],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table('resource_chunks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_resource_chunks_resource_id'))
    op.drop_table('resource_chunks')
