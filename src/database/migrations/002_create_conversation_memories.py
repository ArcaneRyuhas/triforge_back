"""Create conversation memories table

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 12:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Create conversation_memories table
    op.create_table('conversation_memories',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('recent_messages', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_memories_user_id'), 'conversation_memories', ['user_id'], unique=False)
    op.create_index(op.f('ix_conversation_memories_project_id'), 'conversation_memories', ['project_id'], unique=False)
    op.create_index('ix_user_project', 'conversation_memories', ['user_id', 'project_id'], unique=False)

def downgrade():
    op.drop_index('ix_user_project', table_name='conversation_memories')
    op.drop_index(op.f('ix_conversation_memories_project_id'), table_name='conversation_memories')
    op.drop_index(op.f('ix_conversation_memories_user_id'), table_name='conversation_memories')
    op.drop_table('conversation_memories')