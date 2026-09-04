"""add text_content to resources

Revision ID: a1b2c3d4e5f6
Revises: cae68f03c9a8
Create Date: 2026-09-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'cae68f03c9a8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('resources', schema=None) as batch_op:
        batch_op.add_column(sa.Column('text_content', sa.Text(), nullable=True))
        batch_op.alter_column('file_path',
                              existing_type=sa.String(length=512),
                              nullable=True)


def downgrade():
    with op.batch_alter_table('resources', schema=None) as batch_op:
        batch_op.alter_column('file_path',
                              existing_type=sa.String(length=512),
                              nullable=False)
        batch_op.drop_column('text_content')
