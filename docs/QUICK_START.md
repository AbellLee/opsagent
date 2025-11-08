# OpsAgent LLM 多模型支持 - 快速启动指南

## 📋 概述

本指南将帮助您快速启动和使用 OpsAgent 的 LLM 多模型支持功能。

## 🚀 启动步骤

### 1. 启动后端服务

```bash
# 进入后端目录
cd app

# 启动服务
python main.py
```

服务将在 `http://localhost:8000` 启动。

### 2. 启动前端服务

```bash
# 进入前端目录
cd frontend

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run serve
```

前端将在 `http://localhost:8080` 启动。

### 3. 访问应用

打开浏览器访问: `http://localhost:8080`

---

## 🎯 功能使用指南

### 一、配置 LLM 模型

#### 1. 访问配置页面

- 登录后，点击左侧边栏的 **"LLM 配置"** 菜单
- 或直接访问: `http://localhost:8080/llm-config`

#### 2. 创建新配置

点击右上角的 **"新建配置"** 按钮，填写以下信息：

**基本信息**:
- **配置名称**: 例如 "OpenAI GPT-4o-mini"
- **提供商**: 选择 OpenAI、DeepSeek、通义千问等
- **模型名称**: 例如 "gpt-4o-mini"
- **API Key**: 输入您的 API 密钥
- **Base URL**: 自动填充，可修改
- **模型类型**: 选择"聊天模型"或"嵌入模型"

**高级参数**（可选）:
- **Max Tokens**: 最大生成长度（默认 2048）
- **Temperature**: 温度参数（0-2，默认 0.7）
- **Top P**: 核采样参数（0-1，默认 1.0）
- **Frequency Penalty**: 频率惩罚（-2 到 2，默认 0）
- **Presence Penalty**: 存在惩罚（-2 到 2，默认 0）

**其他设置**:
- **描述**: 配置说明（可选）
- **激活状态**: 是否激活此配置
- **设为默认**: 是否设为默认配置

#### 3. 测试配置

创建配置后，点击 **"测试"** 按钮验证配置是否正确。

#### 4. 管理配置

- **编辑**: 点击"编辑"按钮修改配置
- **激活/停用**: 切换配置的激活状态
- **设为默认**: 将配置设为默认（创建会话时自动使用）
- **删除**: 删除不需要的配置

---

### 二、使用模型进行对话

#### 方式 1: 创建新会话时选择模型

1. 点击左侧边栏的 **"+"** 按钮
2. 在弹出的对话框中选择要使用的模型
3. 点击 **"创建"** 按钮
4. 开始与选定的模型对话

#### 方式 2: 使用默认模型

1. 点击左侧边栏的 **"+"** 按钮
2. 不选择模型，直接点击 **"创建"**
3. 系统将使用默认配置的模型

---

### 三、筛选和搜索配置

在 LLM 配置页面，您可以：

- **按提供商筛选**: 选择特定的 LLM 提供商
- **按状态筛选**: 只显示激活或未激活的配置
- **按类型筛选**: 只显示聊天模型或嵌入模型
- **搜索**: 输入关键词搜索配置名称

---

## 📝 配置示例

### OpenAI GPT-4o-mini

```
配置名称: OpenAI GPT-4o-mini
提供商: openai
模型名称: gpt-4o-mini
API Key: sk-...
Base URL: https://api.openai.com/v1
模型类型: 聊天模型
Temperature: 0.7
Max Tokens: 2048
```

### DeepSeek Chat

```
配置名称: DeepSeek Chat
提供商: deepseek
模型名称: deepseek-chat
API Key: sk-...
Base URL: https://api.deepseek.com/v1
模型类型: 聊天模型
Temperature: 0.7
Max Tokens: 2048
```

### 通义千问 Turbo

```
配置名称: 通义千问 Turbo
提供商: tongyi
模型名称: qwen-turbo
API Key: sk-...
Base URL: https://dashscope.aliyuncs.com/compatible-mode/v1
模型类型: 聊天模型
Temperature: 0.7
Max Tokens: 2048
```

### Ollama Llama3（本地）

```
配置名称: Ollama Llama3
提供商: ollama
模型名称: llama3
API Key: (留空)
Base URL: http://localhost:11434
模型类型: 聊天模型
Temperature: 0.7
Max Tokens: 2048
```

---

## 🔧 API 使用示例

### 1. 获取所有配置

```bash
curl http://localhost:8000/api/llm-configs/
```

### 2. 获取默认配置

```bash
curl http://localhost:8000/api/llm-configs/default?is_embedding=false
```

### 3. 创建配置

```bash
curl -X POST http://localhost:8000/api/llm-configs/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenAI GPT-4o-mini",
    "provider": "openai",
    "model_name": "gpt-4o-mini",
    "api_key": "sk-...",
    "base_url": "https://api.openai.com/v1",
    "is_embedding": false,
    "is_active": true,
    "is_default": true
  }'
```

### 4. 使用指定模型创建会话

```bash
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "llm_config_id": "dbb4c325-c30d-4c14-bfc7-1a363cd3da3a"
  }'
```

### 5. 使用 Dify API 发送消息（指定模型）

```bash
curl -X POST http://localhost:8000/v1/chat-messages \
  -H "Content-Type: application/json" \
  -d '{
    "query": "你好",
    "user": "test_user",
    "response_mode": "blocking",
    "model_config_id": "dbb4c325-c30d-4c14-bfc7-1a363cd3da3a"
  }'
```

---

## 🐛 常见问题

### 1. 配置测试失败

**可能原因**:
- API Key 不正确
- Base URL 不正确
- 网络连接问题
- 模型名称错误

**解决方法**:
- 检查 API Key 是否有效
- 验证 Base URL 是否正确
- 检查网络连接
- 确认模型名称拼写正确

### 2. 创建会话时找不到模型

**可能原因**:
- 没有激活的配置
- 配置被停用

**解决方法**:
- 确保至少有一个配置是激活状态
- 检查配置的激活状态

### 3. 对话没有使用指定的模型

**可能原因**:
- 配置 ID 不正确
- 配置未激活
- 后端回退到默认配置

**解决方法**:
- 检查配置 ID 是否正确
- 确保配置是激活状态
- 查看后端日志确认使用的配置

### 4. 前端无法连接后端

**可能原因**:
- 后端服务未启动
- 端口被占用
- CORS 配置问题

**解决方法**:
- 确保后端服务正在运行
- 检查端口 8000 是否可用
- 检查 CORS 配置

---

## 📚 更多资源

- **重构方案**: `docs/REFACTORING_PLAN.md`
- **第三阶段变更**: `docs/PHASE3_CHANGES.md`
- **第四阶段总结**: `docs/PHASE4_SUMMARY.md`
- **API 文档**: 访问 `http://localhost:8000/docs`

---

## 🎉 开始使用

现在您已经了解了如何使用 OpsAgent 的 LLM 多模型支持功能！

1. 配置您的第一个 LLM 模型
2. 创建一个新会话并选择模型
3. 开始与 AI 助手对话

祝您使用愉快！🚀

