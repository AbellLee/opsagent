-- 创建 LLM 配置表
CREATE TABLE IF NOT EXISTS llm_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    api_key VARCHAR(500),
    base_url VARCHAR(200),
    max_tokens INTEGER NOT NULL DEFAULT 2048,
    temperature FLOAT NOT NULL DEFAULT 0.7,
    top_p FLOAT NOT NULL DEFAULT 1.0,
    frequency_penalty FLOAT NOT NULL DEFAULT 0.0,
    presence_penalty FLOAT NOT NULL DEFAULT 0.0,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_embedding BOOLEAN NOT NULL DEFAULT FALSE,
    extra_config JSONB,
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    CONSTRAINT check_provider CHECK (provider IN ('openai', 'deepseek', 'tongyi', 'ollama', 'vllm', 'doubao', 'zhipu', 'moonshot', 'baidu'))
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_llm_configs_provider ON llm_configs(provider);
CREATE INDEX IF NOT EXISTS idx_llm_configs_is_active ON llm_configs(is_active);
CREATE INDEX IF NOT EXISTS idx_llm_configs_is_default_embedding ON llm_configs(is_default, is_embedding);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_llm_configs_updated_at BEFORE UPDATE ON llm_configs
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

