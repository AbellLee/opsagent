"""add llm_configs table

Revision ID: 001
Revises: 
Create Date: 2025-11-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建 llm_configs 表
    op.create_table(
        'llm_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('api_key', sa.String(length=500), nullable=True),
        sa.Column('base_url', sa.String(length=200), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=False, server_default='2048'),
        sa.Column('temperature', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('top_p', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('frequency_penalty', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('presence_penalty', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_embedding', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('extra_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.CheckConstraint(
            "provider IN ('openai', 'deepseek', 'tongyi', 'ollama', 'vllm', 'doubao', 'zhipu', 'moonshot', 'baidu')",
            name='check_provider'
        )
    )
    
    # 创建索引
    op.create_index('idx_llm_configs_provider', 'llm_configs', ['provider'])
    op.create_index('idx_llm_configs_is_active', 'llm_configs', ['is_active'])
    op.create_index('idx_llm_configs_is_default_embedding', 'llm_configs', ['is_default', 'is_embedding'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_llm_configs_is_default_embedding', table_name='llm_configs')
    op.drop_index('idx_llm_configs_is_active', table_name='llm_configs')
    op.drop_index('idx_llm_configs_provider', table_name='llm_configs')
    
    # 删除表
    op.drop_table('llm_configs')

