"""Add search vectors

Revision ID: a1b2c3d4e5f6
Revises: ec33a17f34b3
Create Date: 2026-02-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'ec33a17f34b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Projects
    op.add_column('projects', sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True))
    op.create_index('ix_projects_search_vector', 'projects', ['search_vector'], unique=False, postgresql_using='gin')
    
    # Tasks
    op.add_column('tasks', sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True))
    op.create_index('ix_tasks_search_vector', 'tasks', ['search_vector'], unique=False, postgresql_using='gin')

    # Messages
    # Note: Messages table is partitioned. Adding column to parent table propagates to children.
    # Indexes on partitioned tables are supported in PG11+.
    op.add_column('messages', sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True))
    op.create_index('ix_messages_search_vector', 'messages', ['search_vector'], unique=False, postgresql_using='gin')

    # Create Triggers for automatic updates
    
    # Project Trigger Function
    op.execute("""
        CREATE FUNCTION projects_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.name, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER tsvectorupdate_projects BEFORE INSERT OR UPDATE
        ON projects FOR EACH ROW EXECUTE FUNCTION projects_search_vector_update();
    """)

    # Task Trigger Function
    op.execute("""
        CREATE FUNCTION tasks_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER tsvectorupdate_tasks BEFORE INSERT OR UPDATE
        ON tasks FOR EACH ROW EXECUTE FUNCTION tasks_search_vector_update();
    """)

    # Message Trigger Function
    # For partitioned tables, triggers must be defined on the partition or the parent (PG13+ supports row triggers on partitioned tables).
    # Assuming PG13+, we can add it to the parent.
    op.execute("""
        CREATE FUNCTION messages_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                to_tsvector('english', coalesce(NEW.content, ''));
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER tsvectorupdate_messages BEFORE INSERT OR UPDATE
        ON messages FOR EACH ROW EXECUTE FUNCTION messages_search_vector_update();
    """)


def downgrade() -> None:
    # Drop Triggers and Functions
    op.execute("DROP TRIGGER IF EXISTS tsvectorupdate_messages ON messages")
    op.execute("DROP FUNCTION IF EXISTS messages_search_vector_update")
    
    op.execute("DROP TRIGGER IF EXISTS tsvectorupdate_tasks ON tasks")
    op.execute("DROP FUNCTION IF EXISTS tasks_search_vector_update")

    op.execute("DROP TRIGGER IF EXISTS tsvectorupdate_projects ON projects")
    op.execute("DROP FUNCTION IF EXISTS projects_search_vector_update")

    # Drop Indexes and Columns
    op.drop_index('ix_messages_search_vector', table_name='messages')
    op.drop_column('messages', 'search_vector')

    op.drop_index('ix_tasks_search_vector', table_name='tasks')
    op.drop_column('tasks', 'search_vector')

    op.drop_index('ix_projects_search_vector', table_name='projects')
    op.drop_column('projects', 'search_vector')
