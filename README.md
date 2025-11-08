# OpsAgent

基于langgraph、fastapi和postgresql构建的Agent系统，集成多种大语言模型，支持记忆、MCP工具和自定义工具功能。

## 功能特性

- 🤖 支持多种大语言模型（通义千问等）
- 💾 PostgreSQL支持的持久化记忆
- 🛠️ MCP工具集成
- 🧰 自定义工具扩展
- 🔐 工具执行审批机制
- ⏹️ 对话中断处理机制
- 🌐 RESTful API接口
- 🖥️ 基于Vue3和Naive UI的前端界面
- 🔌 **Dify API 兼容** - 支持 Dify API 规范，可与 Dify 客户端无缝集成

## 技术栈

- **核心框架**: langgraph
- **Web框架**: fastapi
- **数据库**: postgresql
- **AI模型**: 支持通义千问等多种大语言模型
- **前端框架**: vue3
- **UI库**: naive-ui
- **状态管理**: pinia

## 项目结构

```
opsagent/
├── app/
│   ├── main.py              # FastAPI应用入口
│   ├── init_db.py           # 数据库初始化脚本
│   ├── core/                # 核心配置
│   │   ├── config.py        # 配置管理
│   │   ├── llm.py           # 大语言模型集成
│   │   ├── instances.py     # 实例管理
│   │   ├── logger.py        # 日志配置
│   │   └── user_context.py  # 用户上下文管理
│   ├── models/              # 数据模型
│   │   └── schemas.py       # Pydantic模型定义
│   ├── agent/               # Agent核心逻辑
│   │   ├── state.py         # Agent状态定义
│   │   ├── graph.py         # Agent图定义
│   │   └── tools/           # 工具管理
│   │       ├── __init__.py
│   │       ├── mcp_tools.py # MCP工具集成
│   │       └── custom_tools.py # 自定义工具
│   ├── services/            # 业务服务层
│   │   ├── agent/           # Agent相关服务
│   │   │   ├── handlers.py      # Agent处理函数
│   │   │   ├── interrupt_service.py # 中断服务
│   │   │   └── utils.py         # 工具函数
│   │   └── mcp/             # MCP相关服务
│   └── api/                 # API路由
│       ├── __init__.py      # API路由整合
│       ├── deps.py          # 依赖项
│       └── routes/
│           ├── agent.py     # Agent执行路由
│           ├── sessions.py  # 会话管理路由
│           ├── tools.py     # 工具管理路由
│           ├── users.py     # 用户管理路由
│           ├── approvals.py # 审批管理路由
│           ├── tasks.py     # 任务管理路由
│           ├── interrupts.py # 中断处理路由
│           └── mcp_config.py # MCP配置路由
├── frontend/                # 前端项目
│   ├── public/              # 静态资源
│   ├── src/                 # 源代码
│   │   ├── views/           # 页面组件
│   │   │   ├── ChatView.vue     # 聊天界面
│   │   │   ├── LoginView.vue    # 登录界面
│   │   │   ├── RegisterView.vue # 注册界面
│   │   │   └── WelcomeView.vue  # 欢迎界面
│   │   ├── components/      # 可复用组件
│   │   │   ├── AppHeader.vue         # 应用头部
│   │   │   ├── AppSidebar.vue        # 应用侧边栏
│   │   │   ├── ChatMessage.vue       # 聊天消息组件
│   │   │   ├── MessageInput.vue      # 消息输入组件
│   │   │   ├── SessionList.vue       # 会话列表组件
│   │   │   ├── UserMenu.vue          # 用户菜单组件
│   │   │   ├── TaskList.vue          # 任务列表组件
│   │   │   ├── TaskItem.vue          # 任务项组件
│   │   │   ├── UserConfirmationDialog.vue # 用户确认对话框
│   │   │   └── MCPConfigPanel.vue    # MCP配置面板
│   │   ├── stores/          # 状态管理
│   │   │   ├── session.js        # 会话状态管理
│   │   │   └── user.js           # 用户状态管理
│   │   ├── api/             # API调用封装
│   │   │   └── index.js          # API接口封装
│   │   ├── composables/     # 组合式函数
│   │   │   └── useScrollManager.js # 滚动管理
│   │   ├── utils/           # 工具函数
│   │   │   └── markdown.js       # Markdown处理工具
│   │   ├── constants/       # 常量定义
│   │   │   └── messageTypes.js   # 消息类型常量
│   │   ├── router/          # 路由配置
│   │   │   └── index.js          # 路由配置文件
│   │   ├── styles/          # 样式文件
│   │   │   └── global.css        # 全局样式
│   │   ├── App.vue          # 根组件
│   │   └── main.js          # 入口文件
│   ├── package.json         # 项目依赖
│   └── vue.config.js        # Vue配置
├── requirements.txt         # 后端项目依赖
└── README.md               # 项目说明
```

## 快速开始

### 1. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写必要的配置
```

环境变量配置项：
- `DATABASE_URL`: PostgreSQL数据库连接字符串
- `API_KEY`: API访问密钥（可选）
- `LLM_TYPE`: 大语言模型类型（如：tongyi）
- `LLM_API_KEY`: 大语言模型API密钥
- `LLM_MODEL`: 大语言模型名称
- `LLM_EMBEDDING_MODEL`: 嵌入模型名称
- `LLM_BASE_URL`: LLM API基础URL（可选）
- `LLM_TIMEOUT`: LLM调用超时时间（秒，默认60）
- `LLM_MAX_RETRIES`: LLM调用最大重试次数（默认2）
- `DEBUG`: 调试模式（默认：False）
- `LOG_LEVEL`: 日志级别（默认：INFO）

### 3. 初始化数据库

```bash
cd app
python init_db.py
```

### 4. 启动后端服务

```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

或者

```bash
cd app
python main.py
```

### 5. 安装前端依赖

```bash
cd frontend
npm install
```

### 6. 启动前端服务

```bash
cd frontend
npm run serve
```

## API接口

主要API接口包括：

### 会话管理
- `POST /api/sessions` - 创建新会话
- `GET /api/sessions/{session_id}` - 获取会话信息
- `PUT /api/sessions/{session_id}/name` - 更新会话名称
- `DELETE /api/sessions/{session_id}` - 删除会话
- `GET /api/sessions` - 列出用户的所有会话

### Agent执行
- `POST /api/sessions/{session_id}/chat` - 与Agent聊天（支持连续对话）
- `POST /api/sessions/{session_id}/execute` - 执行Agent任务

### 工具管理
- `GET /api/tools` - 列出所有可用工具
- `GET /api/tools/{tool_id}` - 获取特定工具详情
- `PUT /api/tools/{tool_id}/approval` - 设置工具审批配置

### 审批管理
- `GET /api/approvals` - 列出所有待审批项
- `POST /api/approvals` - 请求工具执行审批
- `POST /api/approvals/{approval_id}/approve` - 批准工具执行
- `POST /api/approvals/{approval_id}/reject` - 拒绝工具执行

### 任务管理
- `GET /api/tasks` - 获取任务列表
- `POST /api/tasks/{task_id}/cancel` - 取消任务

### 用户管理
- `POST /api/users` - 用户注册
- `POST /api/users/login` - 用户登录
- `GET /api/users/profile` - 获取用户信息
- `PUT /api/users/profile` - 更新用户信息

### 中断处理
- `POST /api/interrupts/{session_id}` - 中断指定会话的对话

### MCP配置管理
- `GET /api/mcp-configs` - 获取MCP配置列表
- `POST /api/mcp-configs` - 创建MCP配置
- `PUT /api/mcp-configs/{config_id}` - 更新MCP配置
- `DELETE /api/mcp-configs/{config_id}` - 删除MCP配置
- `POST /api/mcp-configs/{config_id}/enable` - 启用MCP配置
- `POST /api/mcp-configs/{config_id}/disable` - 禁用MCP配置

### Dify 兼容 API
- `POST /v1/chat-messages` - 发送聊天消息（兼容 Dify API）
- `GET /v1/conversations/{conversation_id}` - 获取会话信息
- `DELETE /v1/conversations/{conversation_id}` - 删除会话

详细的 Dify API 使用文档请参考：[Dify API 兼容性文档](docs/DIFY_API_COMPATIBILITY.md)

## 数据库表结构

### 用户表 (users)
存储用户基本信息

### 用户会话关系表 (user_sessions)
关联用户和会话

### 工具审批配置表 (tool_approval_config)
配置工具执行审批规则

### MCP服务器配置表 (mcp_server_configs)
存储MCP服务器配置信息

### 任务表 (tasks)
存储用户任务信息

### 检查点表
由langgraph自动创建和管理，用于持久化Agent状态

## 许可证

[MIT License](LICENSE)