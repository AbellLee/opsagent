# 多模态消息格式规范

## 快速参考

### ✅ 正确格式 (LangChain 标准)

```json
{
    "type": "user",
    "content": [
        {
            "type": "text",
            "text": "这个是什么?"  // ✅ 使用 "text" 字段
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "data:image/jpeg;base64,..."
            }
        }
    ]
}
```

### ❌ 错误格式

```json
{
    "type": "user",
    "content": [
        {
            "type": "text",
            "content": "这个是什么?"  // ❌ 不要使用 "content" 字段
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "data:image/jpeg;base64,..."
            }
        }
    ]
}
```

## 详细说明

### 1. 纯文本消息

```json
{
    "type": "user",
    "content": "这是一条纯文本消息"  // 字符串格式
}
```

### 2. 文本 + 图片消息

```json
{
    "type": "user",
    "content": [  // 数组格式
        {
            "type": "text",
            "text": "请分析这张图片"  // 注意: 使用 "text" 字段
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
            }
        }
    ]
}
```

### 3. 纯图片消息

```json
{
    "type": "user",
    "content": [  // 数组格式
        {
            "type": "image_url",
            "image_url": {
                "url": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
            }
        }
    ]
}
```

### 4. 多张图片消息

```json
{
    "type": "user",
    "content": [
        {
            "type": "text",
            "text": "比较这两张图片"
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "data:image/jpeg;base64,..."
            }
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "data:image/png;base64,..."
            }
        }
    ]
}
```

## 前端实现

### 发送消息 (MessageInput.vue)

```javascript
// 构建多模态消息
const userMessageContent = []

// 添加文本
if (messageContent) {
    userMessageContent.push({
        type: 'text',
        text: messageContent  // ✅ 使用 "text" 字段
    })
}

// 添加图片
images.forEach(img => {
    userMessageContent.push({
        type: 'image_url',
        image_url: {
            url: img.url
        }
    })
})
```

### 显示消息 (ChatMessage.vue)

```vue
<template>
  <div v-for="(item, index) in message.content" :key="index">
    <!-- 文本项 -->
    <div v-if="item.type === 'text'">
      <!-- 兼容 content 和 text 两种格式 -->
      <div v-html="parseMarkdown(item.content || item.text || '')"></div>
    </div>
    
    <!-- 图片项 -->
    <div v-else-if="item.type === 'image_url'">
      <img :src="getImageUrl(item)" alt="图片" />
    </div>
  </div>
</template>
```

## 后端实现

### 构建消息 (app/services/agent/utils.py)

```python
from langchain_core.messages import HumanMessage

def build_agent_inputs(message: str, session_id: UUID, files: List[Dict] = None):
    if files and len(files) > 0:
        # 多模态消息
        content = []
        
        # 添加文本
        if message and message.strip():
            content.append({
                "type": "text",
                "text": message.strip()  # ✅ 使用 "text" 字段
            })
        
        # 添加图片
        for file in files:
            if file.get("type") == "image":
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": file.get("url") or file.get("data")
                    }
                })
        
        human_message = HumanMessage(content=content)
    else:
        # 纯文本消息
        human_message = HumanMessage(content=message.strip())
    
    return {"messages": [human_message]}
```

## API 接口

### 请求格式

```http
POST /api/sessions/{session_id}/chat
Content-Type: application/json

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

### 响应格式

```json
{
    "response": {
        "id": "msg-123",
        "type": "assistant",
        "content": [
            {
                "type": "text",
                "content": "这是一只猫的图片..."
            }
        ],
        "timestamp": "2025-11-08T21:30:59.591544"
    }
}
```

## 字段对照表

| 消息类型 | content 类型 | 文本字段 | 图片字段 |
|---------|-------------|---------|---------|
| 纯文本 | `string` | - | - |
| 多模态 | `array` | `text` | `image_url.url` |

## 常见错误

### ❌ 错误 1: 使用 content 字段存储文本

```javascript
// 错误
{
    type: 'text',
    content: '文本内容'  // ❌
}

// 正确
{
    type: 'text',
    text: '文本内容'  // ✅
}
```

### ❌ 错误 2: 图片 URL 格式错误

```javascript
// 错误
{
    type: 'image_url',
    url: 'data:image/jpeg;base64,...'  // ❌
}

// 正确
{
    type: 'image_url',
    image_url: {
        url: 'data:image/jpeg;base64,...'  // ✅
    }
}
```

### ❌ 错误 3: 混用字符串和数组格式

```javascript
// 错误
{
    type: 'user',
    content: '文本' + [图片对象]  // ❌
}

// 正确 - 纯文本
{
    type: 'user',
    content: '文本'  // ✅
}

// 正确 - 多模态
{
    type: 'user',
    content: [
        {type: 'text', text: '文本'},
        {type: 'image_url', image_url: {url: '...'}}
    ]  // ✅
}
```

## 兼容性说明

### 前端显示组件兼容性

为了保持向后兼容,前端显示组件同时支持:
- `item.text` (LangChain 标准,推荐)
- `item.content` (旧格式,兼容)

```javascript
const textContent = item.content || item.text || ''
```

### 建议

1. **新代码**: 使用 `text` 字段(LangChain 标准)
2. **旧代码**: 逐步迁移到 `text` 字段
3. **显示组件**: 保持兼容性,同时支持两种格式

## 参考资源

- [LangChain 多模态消息文档](https://python.langchain.com/docs/modules/model_io/chat/multimodal)
- [OpenAI Vision API 文档](https://platform.openai.com/docs/guides/vision)
- [Claude 3 Vision 文档](https://docs.anthropic.com/claude/docs/vision)

## 总结

**核心原则**:
1. ✅ 文本使用 `text` 字段,不是 `content`
2. ✅ 图片使用 `image_url.url` 嵌套结构
3. ✅ 多模态消息使用数组格式
4. ✅ 纯文本消息使用字符串格式
5. ✅ 遵循 LangChain 标准格式

