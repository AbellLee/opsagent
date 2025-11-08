# Agent 图片支持功能实现总结

## 实现日期
2025-11-08

## 功能概述
为 OpsAgent 系统增加了多模态支持,允许用户在对话中上传和发送图片,Agent 可以理解和分析图片内容。

## 修改的文件

### 后端修改

#### 1. `app/models/schemas.py`
**修改内容:**
- 在 `AgentChatRequest` 类中添加了 `files` 字段
- 支持接收文件列表,每个文件包含 type 和 url/data 字段

**代码变更:**
```python
class AgentChatRequest(BaseModel):
    """Agent聊天请求模型"""
    message: str
    response_mode: str = Field(default="blocking", ...)
    tools: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None
    files: Optional[List[Dict[str, Any]]] = Field(None, description="上传的文件列表，支持图片等多模态内容")
```

#### 2. `app/services/agent/utils.py`
**修改内容:**
- 更新 `build_agent_inputs` 函数,添加 `files` 参数
- 实现多模态消息构建逻辑
- 支持文本+图片、纯图片等多种组合

**核心逻辑:**
```python
def build_agent_inputs(message: str, session_id: UUID, user_id: str = "default_user", files: List[Dict[str, Any]] = None):
    if files and len(files) > 0:
        # 多模态消息: 构建内容数组
        content = []
        if message and message.strip():
            content.append({"type": "text", "text": message.strip()})
        
        for file in files:
            if file.get("type") == "image":
                content.append({
                    "type": "image_url",
                    "image_url": {"url": file.get("url") or file.get("data")}
                })
        
        human_message = HumanMessage(content=content)
    else:
        # 纯文本消息
        human_message = HumanMessage(content=message.strip())
```

#### 3. `app/api/routes/agent.py`
**修改内容:**
- 更新 `/api/sessions/{session_id}/chat` 路由
- 将 `request.files` 传递给 `build_agent_inputs` 函数

**代码变更:**
```python
inputs = build_agent_inputs(request.message, session_id, str(user_id), request.files)
```

### 前端修改

#### 4. `frontend/src/components/ChatMessage.vue`
**修改内容:**
- 添加图片显示支持
- 在消息内容序列中支持 `image_url` 类型
- 添加 `getImageUrl` 方法处理不同格式的图片 URL

**新增代码:**
```vue
<!-- 文本项 - 兼容 content 和 text 字段 -->
<div v-else-if="item.type === 'text'" class="text-response-item">
  <div class="text-content" v-html="parseMarkdown(item.content || item.text || '')"></div>
</div>

<!-- 图片项 -->
<div v-else-if="item.type === 'image_url'" class="image-item">
  <img :src="getImageUrl(item)" alt="图片" class="message-image" />
</div>
```

**样式:**
```css
.message-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  cursor: pointer;
  transition: transform 0.2s ease;
}
```

#### 5. `frontend/src/components/MessageInput.vue`
**修改内容:**
- 添加图片上传按钮
- 实现图片预览功能
- 支持多张图片上传
- 将图片转换为 base64 格式
- 更新发送逻辑以包含图片数据

**新增功能:**
1. **图片上传按钮**
   ```vue
   <input ref="fileInputRef" type="file" accept="image/*" multiple />
   <n-button @click="triggerFileInput">
     <图片图标>
   </n-button>
   ```

2. **图片预览区域**
   ```vue
   <div class="image-preview-container">
     <div v-for="(image, index) in uploadedImages" class="image-preview-item">
       <img :src="image.url" />
       <n-button @click="removeImage(index)">删除</n-button>
     </div>
   </div>
   ```

3. **图片处理方法**
   - `triggerFileInput()`: 触发文件选择
   - `handleFileSelect()`: 处理文件选择事件
   - `fileToBase64()`: 将文件转换为 base64
   - `removeImage()`: 删除已上传的图片

4. **发送逻辑更新**
   ```javascript
   const sendMessage = async () => {
     const images = [...uploadedImages.value]
     
     // 构建多模态消息内容
     if (images.length > 0) {
       userMessageContent = []
       if (messageContent) {
         userMessageContent.push({ type: 'text', text: messageContent })  // 使用 text 字段,符合 LangChain 标准
       }
       images.forEach(img => {
         userMessageContent.push({
           type: 'image_url',
           image_url: { url: img.url }
         })
       })
     }
     
     // 发送时包含 files 字段
     await messageAPI.send(sessionStore.sessionId, {
       message: messageContent,
       files: images.map(img => ({ type: 'image', data: img.data })),
       response_mode: responseMode.value
     })
   }
   ```

## 新增文件

### 1. `docs/IMAGE_SUPPORT.md`
完整的用户文档,包括:
- 功能特性说明
- 使用方法
- API 接口文档
- 技术实现细节
- 支持的模型列表
- 示例场景
- 限制和注意事项

### 2. `tests/test_image_support.py`
单元测试文件,包含:
- 纯文本消息测试
- 单张图片消息测试
- 多张图片消息测试
- 只有图片没有文本的测试
- base64 编码图片测试
- 边界情况测试

### 3. `docs/IMAGE_SUPPORT_IMPLEMENTATION.md`
本文档,记录实现细节和变更历史

## 技术要点

### 1. 多模态消息格式
LangChain 的多模态消息格式:
```python
HumanMessage(content=[
    {"type": "text", "text": "文本内容"},
    {"type": "image_url", "image_url": {"url": "图片URL或base64"}}
])
```

### 2. 图片编码
- 前端使用 `FileReader.readAsDataURL()` 将图片转换为 base64
- 格式: `data:image/[format];base64,[data]`
- 支持 URL 和 base64 两种方式

### 3. 兼容性处理
- 保持向后兼容,纯文本消息仍使用字符串格式
- 多模态消息使用数组格式
- 前端组件同时支持两种格式的显示
- **重要**: 文本内容使用 `text` 字段(LangChain 标准),前端同时兼容 `content` 和 `text` 字段

## 测试结果

### 后端测试
```bash
测试1 - 纯文本: 你好
测试2 - 文本+图片: <class 'list'> 2
测试3 - 只有图片: <class 'list'> 1
所有测试通过!
```

### 功能验证
- ✅ 纯文本消息正常工作
- ✅ 文本+图片组合消息正常构建
- ✅ 纯图片消息正常构建
- ✅ 多张图片支持
- ✅ base64 编码正确处理
- ✅ URL 格式正确处理

## 使用限制

1. **文件大小**: 单张图片限制 5MB
2. **模型要求**: 需要使用支持多模态的 LLM 模型
3. **格式支持**: 支持常见图片格式(JPG, PNG, GIF, WebP)
4. **数量限制**: 前端无硬性限制,但建议不超过 10 张

## 支持的模型

以下模型已知支持图片输入:
- OpenAI: gpt-4-vision-preview, gpt-4o, gpt-4o-mini
- Anthropic: claude-3-opus, claude-3-sonnet, claude-3-haiku
- Google: gemini-pro-vision, gemini-1.5-pro
- 阿里: qwen-vl-plus, qwen-vl-max

## 后续改进建议

1. **性能优化**
   - 实现图片压缩以减少传输大小
   - 支持图片懒加载

2. **功能增强**
   - 支持图片 URL 直接输入
   - 图片点击放大预览
   - 支持更多文件类型(PDF, 视频等)
   - 图片历史记录管理

3. **用户体验**
   - 添加上传进度提示
   - 支持拖拽上传
   - 图片编辑功能(裁剪、旋转等)

## 注意事项

1. **模型配置**: 使用前请确保配置的 LLM 模型支持多模态输入
2. **API 密钥**: 某些模型的图片功能可能需要特殊的 API 权限
3. **成本**: 图片输入通常会增加 API 调用成本
4. **隐私**: 图片数据会发送到 LLM 服务提供商,请注意隐私保护

## 总结

本次更新成功为 OpsAgent 添加了完整的图片支持功能,包括:
- ✅ 后端多模态消息处理
- ✅ 前端图片上传和预览
- ✅ 消息显示支持
- ✅ API 接口扩展
- ✅ 完整的文档和测试

用户现在可以在对话中上传图片,让 Agent 分析图片内容,实现更丰富的交互体验。

