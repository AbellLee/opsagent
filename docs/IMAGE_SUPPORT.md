# Agent 图片支持功能

## 概述

Agent 现在支持多模态输入,用户可以在对话中发送图片,Agent 将能够理解和分析图片内容。

## 功能特性

### 1. 图片上传
- 支持多张图片同时上传
- 支持的格式: JPG, PNG, GIF, WebP 等常见图片格式
- 单张图片大小限制: 5MB
- 图片会自动转换为 base64 格式发送

### 2. 图片预览
- 上传后可以在输入框上方预览图片
- 可以删除已上传的图片
- 支持多张图片的预览和管理

### 3. 多模态消息
- 可以同时发送文本和图片
- 也可以只发送图片(不需要文本)
- 图片会作为消息内容的一部分显示

## 使用方法

### 前端使用

1. **上传图片**
   - 点击输入框左侧的图片图标
   - 选择一张或多张图片
   - 图片会显示在输入框上方的预览区域

2. **删除图片**
   - 鼠标悬停在预览图片上
   - 点击右上角的 X 按钮删除

3. **发送消息**
   - 输入文本(可选)
   - 点击发送按钮
   - 图片和文本会一起发送给 Agent

### API 使用

#### 请求格式

```json
POST /api/sessions/{session_id}/chat
{
  "message": "这是什么图片?",
  "files": [
    {
      "type": "image",
      "data": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
    }
  ],
  "response_mode": "streaming"
}
```

#### 字段说明

- `message`: 文本消息内容(可选,如果只发送图片可以为空字符串)
- `files`: 文件列表,每个文件包含:
  - `type`: 文件类型,目前支持 "image"
  - `data`: base64 编码的图片数据,格式为 `data:image/[format];base64,[data]`
  - `url`: 或者使用图片 URL(二选一)
- `response_mode`: 响应模式,可选 "blocking" 或 "streaming"

## 技术实现

### 后端实现

1. **数据模型** (`app/models/schemas.py`)
   - `AgentChatRequest` 添加了 `files` 字段
   - 支持接收文件列表

2. **消息构建** (`app/services/agent/utils.py`)
   - `build_agent_inputs` 函数支持多模态内容
   - 将图片转换为 LangChain 的 `HumanMessage` 格式
   - 消息内容格式(符合 LangChain 标准):
     ```python
     [
       {"type": "text", "text": "文本内容"},  # 注意: 使用 "text" 字段,不是 "content"
       {"type": "image_url", "image_url": {"url": "data:image/..."}}
     ]
     ```

3. **API 路由** (`app/api/routes/agent.py`)
   - 接收 `files` 参数并传递给消息构建函数

### 前端实现

1. **消息显示** (`frontend/src/components/ChatMessage.vue`)
   - 支持显示 `image_url` 类型的内容
   - 支持显示 `text` 类型的内容(同时兼容 `content` 和 `text` 字段)
   - 图片会以合适的大小显示在消息中
   - 支持点击放大(可扩展)

2. **消息输入** (`frontend/src/components/MessageInput.vue`)
   - 添加图片上传按钮
   - 图片预览功能
   - 将图片转换为 base64 并发送

## 支持的模型

图片支持功能需要使用支持多模态的 LLM 模型,例如:

- OpenAI GPT-4 Vision (gpt-4-vision-preview, gpt-4o)
- Claude 3 (Opus, Sonnet, Haiku)
- Google Gemini Pro Vision
- 通义千问 VL (qwen-vl-plus, qwen-vl-max)

**注意**: 请确保配置的模型支持图片输入,否则可能会出现错误。

## 示例场景

1. **图片识别**
   - 用户: [上传一张猫的图片] "这是什么动物?"
   - Agent: "这是一只猫..."

2. **图片分析**
   - 用户: [上传图表] "帮我分析这个图表"
   - Agent: "从图表中可以看出..."

3. **多图对比**
   - 用户: [上传两张图片] "这两张图片有什么区别?"
   - Agent: "第一张图片显示...,第二张图片显示..."

## 限制和注意事项

1. **文件大小**: 单张图片不超过 5MB
2. **模型支持**: 需要使用支持多模态的模型
3. **网络传输**: 图片使用 base64 编码,会增加请求大小
4. **性能**: 大量图片可能影响响应速度

## 未来改进

- [ ] 支持图片 URL 直接输入
- [ ] 支持图片压缩以减少传输大小
- [ ] 支持更多文件类型(PDF, 视频等)
- [ ] 图片点击放大预览
- [ ] 图片历史记录管理

