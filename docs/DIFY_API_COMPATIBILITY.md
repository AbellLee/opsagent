# Dify API 兼容性文档

本项目现已支持 Dify API 兼容接口，允许使用 Dify 客户端或遵循 Dify API 规范的应用直接调用。

## API 端点

### 1. 发送聊天消息

**端点**: `POST /v1/chat-messages`

**请求头**:
```
Content-Type: application/json
Authorization: Bearer {API_KEY}  # 可选，当前版本暂不验证
```

**请求体**:
```json
{
  "inputs": {},
  "query": "你好，请介绍一下你自己",
  "response_mode": "streaming",
  "conversation_id": "",
  "user": "user-123"
}
```

**参数说明**:
- `inputs` (object, 可选): 输入变量，默认为空对象
- `query` (string, 必填): 用户输入的消息内容
- `response_mode` (string, 可选): 响应模式，可选值：
  - `blocking`: 阻塞模式，等待完整响应后返回
  - `streaming`: 流式模式，实时返回响应片段（默认）
- `conversation_id` (string, 可选): 会话ID
  - 为空或不提供时，系统会创建新会话
  - 提供已存在的会话ID时，继续该会话
- `user` (string, 必填): 用户标识符
  - 系统会自动查找或创建对应的用户

### 2. 阻塞模式响应

当 `response_mode` 为 `blocking` 时，返回完整的响应：

```json
{
  "event": "message",
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversation_id": "660e8400-e29b-41d4-a716-446655440001",
  "mode": "chat",
  "answer": "你好！我是一个AI助手...",
  "metadata": {
    "usage": {
      "total_tokens": 150
    }
  },
  "created_at": 1699000000
}
```

### 3. 流式模式响应

当 `response_mode` 为 `streaming` 时，返回 Server-Sent Events (SSE) 流：

**响应头**:
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**事件类型**:

#### 3.1 消息开始事件
```
data: {"event":"message","message_id":"xxx","conversation_id":"xxx","created_at":1699000000}
```

#### 3.2 AI消息片段事件
```
data: {"event":"agent_message","message_id":"xxx","conversation_id":"xxx","answer":"你好","created_at":1699000000}
```

#### 3.3 Agent思考事件（工具调用）
```
data: {"event":"agent_thought","message_id":"xxx","conversation_id":"xxx","thought":"调用工具: search","tool":"search","tool_input":{"query":"天气"},"created_at":1699000000}
```

#### 3.4 工具执行结果事件
```
data: {"event":"agent_thought","message_id":"xxx","conversation_id":"xxx","thought":"工具 search 执行结果","observation":"今天天气晴朗","created_at":1699000000}
```

#### 3.5 消息结束事件
```
data: {"event":"message_end","message_id":"xxx","conversation_id":"xxx","metadata":{"usage":{"total_tokens":0}},"created_at":1699000000}
```

### 4. 获取会话信息

**端点**: `GET /v1/conversations/{conversation_id}`

**响应**:
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Dify Chat",
  "created_at": 1699000000
}
```

### 5. 删除会话

**端点**: `DELETE /v1/conversations/{conversation_id}`

**响应**:
```json
{
  "result": "success"
}
```

## 使用示例

### cURL 示例

#### 阻塞模式
```bash
curl --location --request POST 'http://localhost:8000/v1/chat-messages' \
--header 'Content-Type: application/json' \
--data-raw '{
  "inputs": {},
  "query": "你好，请介绍一下你自己",
  "response_mode": "blocking",
  "conversation_id": "",
  "user": "user-123"
}'
```

#### 流式模式
```bash
curl --location --request POST 'http://localhost:8000/v1/chat-messages' \
--header 'Content-Type: application/json' \
--data-raw '{
  "inputs": {},
  "query": "你好，请介绍一下你自己",
  "response_mode": "streaming",
  "conversation_id": "",
  "user": "user-123"
}'
```

#### 继续已有会话
```bash
curl --location --request POST 'http://localhost:8000/v1/chat-messages' \
--header 'Content-Type: application/json' \
--data-raw '{
  "inputs": {},
  "query": "继续上一个话题",
  "response_mode": "streaming",
  "conversation_id": "660e8400-e29b-41d4-a716-446655440001",
  "user": "user-123"
}'
```

### Python 示例

#### 阻塞模式
```python
import requests
import json

url = "http://localhost:8000/v1/chat-messages"

headers = {
    'Content-Type': 'application/json'
}

data = {
    "inputs": {},
    "query": "你好，请介绍一下你自己",
    "response_mode": "blocking",
    "conversation_id": "",
    "user": "user-123"
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json())
```

#### 流式模式
```python
import requests
import json

url = "http://localhost:8000/v1/chat-messages"

headers = {
    'Content-Type': 'application/json'
}

data = {
    "inputs": {},
    "query": "你好，请介绍一下你自己",
    "response_mode": "streaming",
    "conversation_id": "",
    "user": "user-123"
}

response = requests.post(url, headers=headers, data=json.dumps(data), stream=True)

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            event_data = json.loads(line_str[6:])
            print(event_data)
```

### JavaScript 示例

```javascript
// 流式模式
async function chatWithDify() {
  const response = await fetch('http://localhost:8000/v1/chat-messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      inputs: {},
      query: '你好，请介绍一下你自己',
      response_mode: 'streaming',
      conversation_id: '',
      user: 'user-123'
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const eventData = JSON.parse(line.substring(6));
        console.log(eventData);
        
        if (eventData.event === 'agent_message') {
          // 处理AI消息片段
          console.log('AI回复:', eventData.answer);
        }
      }
    }
  }
}

chatWithDify();
```

## 与原有 API 的映射关系

| Dify API | 原有 API | 说明 |
|----------|----------|------|
| `POST /v1/chat-messages` | `POST /api/sessions/{session_id}/chat` | 聊天接口 |
| `conversation_id` | `session_id` | 会话标识 |
| `query` | `message` | 用户消息 |
| `user` | 自动创建/查找用户 | 用户标识 |

## 注意事项

1. **会话管理**: 
   - 首次调用时不提供 `conversation_id`，系统会自动创建新会话并返回
   - 后续调用时使用返回的 `conversation_id` 来继续对话

2. **用户管理**:
   - 系统会根据 `user` 参数自动创建或查找用户
   - 如果用户不存在，会自动创建一个新用户，邮箱格式为 `{user}@dify.local`

3. **响应模式**:
   - `blocking` 模式适合简单的请求-响应场景
   - `streaming` 模式适合需要实时反馈的场景，特别是长文本生成

4. **兼容性**:
   - 本实现遵循 Dify API 规范，但可能不包含所有 Dify 的高级功能
   - 主要支持基础的聊天对话功能和工具调用

5. **认证**:
   - 当前版本暂未实现 API Key 认证
   - 后续版本会添加完整的认证机制

## 测试建议

1. 使用 Postman 或类似工具测试 API
2. 先测试阻塞模式，确保基本功能正常
3. 再测试流式模式，观察事件流
4. 测试会话连续性，确保上下文保持正确

