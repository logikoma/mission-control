"""Add sub_agents table

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-15 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sub_agents table
    op.create_table(
        'sub_agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('api_key_hash', sa.String(), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timeout_at', sa.DateTime(), nullable=False),
        sa.Column('terminated', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('terminated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_sub_agents_id'), 'sub_agents', ['id'], unique=False)
    op.create_index(op.f('ix_sub_agents_org_id'), 'sub_agents', ['org_id'], unique=False)
    op.create_index(op.f('ix_sub_agents_task_id'), 'sub_agents', ['task_id'], unique=False)
    op.create_index(op.f('ix_sub_agents_project_id'), 'sub_agents', ['project_id'], unique=False)
    
    # Create foreign keys
    op.create_foreign_key(None, 'sub_agents', 'organizations', ['org_id'], ['id'])
    op.create_foreign_key(None, 'sub_agents', 'tasks', ['task_id'], ['id'])
    op.create_foreign_key(None, 'sub_agents', 'projects', ['project_id'], ['id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_sub_agents_project_id'), table_name='sub_agents')
    op.drop_index(op.f('ix_sub_agents_task_id'), table_name='sub_agents')
    op.drop_index(op.f('ix_sub_agents_org_id'), table_name='sub_agents')
    op.drop_index(op.f('ix_sub_agents_id'), table_name='sub_agents')
    op.drop_table('sub_agents')
