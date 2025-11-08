# 第三阶段：API 集成和 Dify 兼容 - 变更说明

## 📋 概述

第三阶段实现了 LLM 多模型支持与现有 API 的集成，使用户可以在创建会话和发送消息时选择使用哪个 LLM 配置。

## 🎯 主要变更

### 1. Dify API 增强

#### 1.1 请求模型更新

**文件**: `app/models/schemas.py`

在 `DifyChatRequest` 模型中添加了 `model_config_id` 字段：

```python
class DifyChatRequest(BaseModel):
    inputs: Optional[Dict[str, Any]] = Field(default_factory=dict)
    query: str = Field(...)
    response_mode: str = Field(default="blocking")
    conversation_id: Optional[str] = Field(None)
    user: str = Field(...)
    files: Optional[List[Dict[str, Any]]] = Field(None)
    model_config_id: Optional[str] = Field(None, description="LLM配置ID，为空时使用默认配置")  # 新增
```

#### 1.2 Dify 路由更新

**文件**: `app/api/routes/dify.py`

**变更内容**:

1. **会话创建时验证和保存 LLM 配置**（第 166-224 行）
   - 验证 `model_config_id` 格式和有效性
   - 检查配置是否存在且激活
   - 在创建会话时保存 `llm_config_id` 到数据库

2. **流式响应支持模型配置**（第 19-47 行）
   - `stream_dify_response()` 函数新增 `model_config_id` 参数
   - 将 `model_config_id` 添加到 LangGraph 配置中

3. **阻塞响应支持模型配置**（第 226-258 行）
   - 在调用 `handle_blocking_chat()` 前将 `model_config_id` 添加到配置

**使用示例**:

```bash
# 使用指定的 LLM 配置
curl -X POST http://localhost:8000/v1/chat-messages \
  -H "Content-Type: application/json" \
  -d '{
    "query": "你好",
    "user": "test_user",
    "response_mode": "blocking",
    "model_config_id": "dbb4c325-c30d-4c14-bfc7-1a363cd3da3a"
  }'

# 不指定配置（使用默认）
curl -X POST http://localhost:8000/v1/chat-messages \
  -H "Content-Type: application/json" \
  -d '{
    "query": "你好",
    "user": "test_user",
    "response_mode": "blocking"
  }'
```

### 2. 会话 API 增强

#### 2.1 会话模型更新

**文件**: `app/models/schemas.py`

```python
class SessionCreate(BaseModel):
    user_id: UUID
    llm_config_id: Optional[UUID] = Field(None, description="LLM配置ID，为空时使用默认配置")  # 新增

class Session(BaseModel):
    session_id: UUID
    user_id: UUID
    session_name: str = "新建对话"
    llm_config_id: Optional[UUID] = None  # 新增
    created_at: datetime
    expires_at: datetime
```

#### 2.2 会话路由更新

**文件**: `app/api/routes/sessions.py`

**变更内容**:

1. **创建会话时支持 LLM 配置**（第 11-60 行）
   - 验证 `llm_config_id` 有效性
   - 保存到数据库

2. **获取会话时返回 LLM 配置**（第 62-97 行）
   - 查询时包含 `llm_config_id` 字段
   - 响应中返回配置 ID

3. **列出会话时返回 LLM 配置**（第 176-208 行）
   - 查询时包含 `llm_config_id` 字段
   - 响应中返回配置 ID

**使用示例**:

```bash
# 创建会话（指定 LLM 配置）
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "llm_config_id": "dbb4c325-c30d-4c14-bfc7-1a363cd3da3a"
  }'

# 创建会话（使用默认配置）
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### 3. Agent Graph 增强

#### 3.1 LLM 获取逻辑更新

**文件**: `app/agent/graph.py`

**新增函数**: `get_llm_from_config(config: RunnableConfig)`

**功能**:
- 从 LangGraph 配置中读取 `model_config_id`
- 如果指定了配置 ID，使用数据库配置
- 否则回退到环境变量配置（向后兼容）

**变更内容**:

```python
def get_llm_from_config(config: RunnableConfig):
    """从配置中获取 LLM 实例"""
    model_config_id = config.get("configurable", {}).get("model_config_id")
    
    if model_config_id:
        # 使用数据库配置
        db = next(get_db_sqlalchemy())
        try:
            llm_manager = LLMManager(db)
            config_id = UUID(model_config_id)
            llm, embedding = llm_manager.get_llm_and_embedding(chat_config_id=config_id)
            return llm, embedding
        finally:
            db.close()
    else:
        # 使用默认配置（环境变量）
        return get_llm()
```

**调用位置**: `call_model()` 函数（第 88-94 行）

```python
# 初始化 LLM（支持从配置中读取 model_config_id）
try:
    llm, _ = get_llm_from_config(config)
except LLMInitializationError as e:
    logger.error(f"LLM初始化失败: {e}")
    return {"messages": [AIMessage(content=f"模型初始化失败: {str(e)}")]}
```

## 🔄 数据流

### 1. Dify API 流程

```
用户请求 (带 model_config_id)
    ↓
验证 model_config_id
    ↓
创建/获取会话 (保存 llm_config_id)
    ↓
构建 LangGraph 配置 (添加 model_config_id)
    ↓
调用 Agent Graph
    ↓
get_llm_from_config() 读取配置
    ↓
LLMManager 获取对应的 LLM 实例
    ↓
使用指定模型生成回复
```

### 2. 会话 API 流程

```
创建会话请求 (带 llm_config_id)
    ↓
验证 llm_config_id
    ↓
保存到 user_sessions 表
    ↓
返回会话信息 (包含 llm_config_id)
```

## 🧪 测试

### 测试脚本

**文件**: `app/scripts/test_phase3_integration.py`

**测试内容**:
1. LLM 配置 API 测试
2. 创建带 LLM 配置的会话
3. 创建不指定 LLM 配置的会话（使用默认）
4. Dify API 阻塞模式测试（指定模型）
5. Dify API 流式模式测试（指定模型）

**运行方式**:

```bash
# 确保服务器正在运行
cd app && python main.py

# 在另一个终端运行测试
python app/scripts/test_phase3_integration.py
```

## 📊 数据库变更

### user_sessions 表

已在第一阶段添加 `llm_config_id` 字段：

```sql
ALTER TABLE user_sessions 
ADD COLUMN llm_config_id UUID REFERENCES llm_configs(id);
```

## 🔒 向后兼容性

### 1. 可选参数

所有新增的 `model_config_id` / `llm_config_id` 字段都是可选的：
- 如果不提供，系统使用默认配置
- 现有代码无需修改即可继续工作

### 2. 环境变量配置

`get_llm_from_config()` 函数会在以下情况回退到环境变量配置：
- 未指定 `model_config_id`
- 数据库配置加载失败
- 指定的配置不存在或未激活

### 3. 数据库字段

`user_sessions.llm_config_id` 字段允许为 NULL：
- 旧会话没有此字段（NULL）
- 新会话可以选择性指定

## 🎯 下一步

第四阶段将实现前端功能：
1. LLM 配置管理页面
2. 聊天界面的模型选择组件
3. 会话列表显示使用的模型
4. 模型切换功能

## 📝 注意事项

1. **性能考虑**: 每次调用 `get_llm_from_config()` 都会创建新的数据库连接，在高并发场景下可能需要优化（使用连接池或缓存）

2. **错误处理**: 如果指定的 `model_config_id` 无效，系统会：
   - Dify API: 返回 400 错误
   - Agent Graph: 回退到默认配置并记录警告日志

3. **日志记录**: 所有模型选择操作都会记录日志，便于调试和审计

4. **测试建议**: 
   - 测试指定有效配置 ID
   - 测试指定无效配置 ID
   - 测试不指定配置 ID（默认行为）
   - 测试流式和阻塞两种模式

