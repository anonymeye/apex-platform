"""Add agents, knowledge bases, tools, and documents

Revision ID: ce486ea2174c
Revises: 43ad7097345b
Create Date: 2026-01-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ce486ea2174c'
down_revision: Union[str, None] = '43ad7097345b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create knowledge_bases table first (no dependencies on other new tables)
    op.create_table('knowledge_bases',
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('slug', sa.String(length=255), nullable=False),
    sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_bases_slug'), 'knowledge_bases', ['slug'], unique=False)
    op.create_index(op.f('ix_knowledge_bases_organization_id'), 'knowledge_bases', ['organization_id'], unique=False)
    
    # Create connections table (depends on organizations)
    op.create_table(
        'connections',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('connection_type', sa.String(length=50), nullable=False),  # vendor_api | openai_compatible
        sa.Column('provider', sa.String(length=50), nullable=False),  # openai | anthropic | groq | openai_compatible
        sa.Column('base_url', sa.String(length=500), nullable=True),
        sa.Column('auth_type', sa.String(length=50), nullable=False),  # env | bearer | none
        sa.Column('api_key_env_var', sa.String(length=255), nullable=True),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_connections_organization_id'), 'connections', ['organization_id'], unique=False)
    op.create_index(op.f('ix_connections_provider'), 'connections', ['provider'], unique=False)

    # Create model_refs table (depends on connections and organizations)
    op.create_table(
        'model_refs',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('runtime_id', sa.String(length=255), nullable=False),  # model identifier expected by runtime
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_model_refs_organization_id'), 'model_refs', ['organization_id'], unique=False)
    op.create_index(op.f('ix_model_refs_connection_id'), 'model_refs', ['connection_id'], unique=False)

    # Create agents table (depends on organizations and model_refs)
    op.create_table(
        'agents',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('model_ref_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('system_message', sa.Text(), nullable=True),
        sa.Column('max_iterations', sa.Integer(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['model_ref_id'], ['model_refs.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_agents_organization_id'), 'agents', ['organization_id'], unique=False)
    op.create_index(op.f('ix_agents_model_ref_id'), 'agents', ['model_ref_id'], unique=False)
    
    # Create documents table (depends on knowledge_bases)
    op.create_table('documents',
    sa.Column('knowledge_base_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('source', sa.String(length=500), nullable=True),
    sa.Column('chunk_index', sa.Integer(), nullable=True),
    sa.Column('vector_id', sa.String(length=255), nullable=True),
    sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_knowledge_base_id'), 'documents', ['knowledge_base_id'], unique=False)
    op.create_index(op.f('ix_documents_vector_id'), 'documents', ['vector_id'], unique=False)
    
    # Create tools table (depends on knowledge_bases and organizations)
    op.create_table('tools',
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('tool_type', sa.String(length=50), nullable=False),
    sa.Column('knowledge_base_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('rag_template', sa.Text(), nullable=True),
    sa.Column('rag_k', sa.Integer(), nullable=True),
    sa.Column('auto_created', sa.Boolean(), nullable=False),
    sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tools_name'), 'tools', ['name'], unique=True)
    op.create_index(op.f('ix_tools_tool_type'), 'tools', ['tool_type'], unique=False)
    op.create_index(op.f('ix_tools_knowledge_base_id'), 'tools', ['knowledge_base_id'], unique=False)
    op.create_index(op.f('ix_tools_organization_id'), 'tools', ['organization_id'], unique=False)
    
    # Create agent_tools table (depends on agents and tools)
    op.create_table('agent_tools',
    sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_tools_agent_id'), 'agent_tools', ['agent_id'], unique=False)
    op.create_index(op.f('ix_agent_tools_tool_id'), 'agent_tools', ['tool_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order of dependencies
    op.drop_index(op.f('ix_agent_tools_tool_id'), table_name='agent_tools')
    op.drop_index(op.f('ix_agent_tools_agent_id'), table_name='agent_tools')
    op.drop_table('agent_tools')
    
    op.drop_index(op.f('ix_tools_organization_id'), table_name='tools')
    op.drop_index(op.f('ix_tools_knowledge_base_id'), table_name='tools')
    op.drop_index(op.f('ix_tools_tool_type'), table_name='tools')
    op.drop_index(op.f('ix_tools_name'), table_name='tools')
    op.drop_table('tools')
    
    op.drop_index(op.f('ix_documents_vector_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_knowledge_base_id'), table_name='documents')
    op.drop_table('documents')
    
    op.drop_index(op.f('ix_agents_model_ref_id'), table_name='agents')
    op.drop_index(op.f('ix_agents_organization_id'), table_name='agents')
    op.drop_table('agents')

    op.drop_index(op.f('ix_model_refs_connection_id'), table_name='model_refs')
    op.drop_index(op.f('ix_model_refs_organization_id'), table_name='model_refs')
    op.drop_table('model_refs')

    op.drop_index(op.f('ix_connections_provider'), table_name='connections')
    op.drop_index(op.f('ix_connections_organization_id'), table_name='connections')
    op.drop_table('connections')
    
    op.drop_index(op.f('ix_knowledge_bases_organization_id'), table_name='knowledge_bases')
    op.drop_index(op.f('ix_knowledge_bases_slug'), table_name='knowledge_bases')
    op.drop_table('knowledge_bases')
