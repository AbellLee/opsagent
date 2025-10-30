-- Dify Agent 配置表
CREATE TABLE IF NOT EXISTS dify_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    agent_type VARCHAR(50) NOT NULL, -- 'chatbot', 'workflow', 'agent'
    dify_app_id VARCHAR(255) NOT NULL, -- Dify 平台的 App ID
    api_key VARCHAR(500) NOT NULL, -- Dify API Key
    base_url VARCHAR(500) DEFAULT 'https://api.dify.ai/v1', -- Dify API 基础 URL
    
    -- Agent 能力描述（用于 Supervisor 路由决策）
    capabilities TEXT[], -- 能力标签，如 ['knowledge_base', 'document_qa', 'customer_service']
    keywords TEXT[], -- 关键词，用于匹配用户意图
    
    -- 配置参数
    config JSONB DEFAULT '{}', -- 额外配置，如温度、最大token等
    input_schema JSONB DEFAULT NULL, -- inputs 参数的 Schema 定义

    -- 状态管理
    enabled BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0, -- 优先级，数字越大优先级越高
    
    -- 元数据
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_dify_agents_enabled ON dify_agents(enabled);
CREATE INDEX IF NOT EXISTS idx_dify_agents_type ON dify_agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_dify_agents_priority ON dify_agents(priority DESC);

-- 创建 GIN 索引用于数组搜索
CREATE INDEX IF NOT EXISTS idx_dify_agents_capabilities ON dify_agents USING GIN(capabilities);
CREATE INDEX IF NOT EXISTS idx_dify_agents_keywords ON dify_agents USING GIN(keywords);

-- 添加注释
COMMENT ON TABLE dify_agents IS 'Dify Agent 配置表，用于管理和路由到不同的 Dify Agent';
COMMENT ON COLUMN dify_agents.agent_type IS 'Agent 类型: chatbot(对话型), workflow(工作流), agent(智能体)';
COMMENT ON COLUMN dify_agents.capabilities IS '能力标签数组，用于 Supervisor 路由决策';
COMMENT ON COLUMN dify_agents.keywords IS '关键词数组，用于匹配用户输入';
COMMENT ON COLUMN dify_agents.priority IS '优先级，当多个 Agent 匹配时选择优先级高的';
COMMENT ON COLUMN dify_agents.input_schema IS 'inputs 参数的 Schema 定义，格式: {"param_name": {"type": "string", "required": true, "description": "说明"}}';

-- 插入示例数据（可选）
INSERT INTO dify_agents (name, description, agent_type, dify_app_id, api_key, capabilities, keywords, priority)
VALUES 
    ('知识库助手', '专门处理知识库查询和文档问答', 'chatbot', 'your-kb-app-id', 'your-kb-api-key', 
     ARRAY['knowledge_base', 'document_qa', 'search'], 
     ARRAY['知识库', '文档', '查询', '搜索', '资料'], 
     10),
    ('工作流执行器', '执行复杂的工作流任务', 'workflow', 'your-wf-app-id', 'your-wf-api-key', 
     ARRAY['workflow', 'automation', 'task_execution'], 
     ARRAY['工作流', '自动化', '流程', '执行'], 
     5)
ON CONFLICT DO NOTHING;

