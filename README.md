# OpsAgent

基于langgraph、fastapi和postgresql构建的Agent系统，集成通义语言模型，支持记忆、MCP工具和自定义工具功能。

## 功能特性

- 🤖 基于通义语言模型的智能对话
- 💾 PostgreSQL支持的持久化记忆
- 🛠️ MCP工具集成
- 🧰 自定义工具扩展
- 🔐 工具执行审批机制
- 🌐 RESTful API接口
- 🖥️ 基于Vue3和Naive UI的前端界面

## 技术栈

- **核心框架**: langgraph
- **Web框架**: fastapi
- **数据库**: postgresql
- **AI模型**: 通义语言模型
- **前端框架**: vue3
- **UI库**: naive-ui

## 项目结构

```
opsagent/
├── app/
│   ├── main.py              # FastAPI应用入口
│   ├── api/                 # API路由
│   │   ├── routes/
│   │   │   ├── sessions.py  # 会话管理路由
│   │   │   ├── tools.py     # 工具管理路由
│   │   │   ├── users.py     # 用户管理路由
│   │   │   ├── agent.py     # Agent执行路由
│   │   │   └── approvals.py # 审批管理路由
│   ├── core/                # 核心配置
│   │   ├── config.py        # 配置管理
│   │   └── logger.py        # 日志配置
│   ├── models/              # 数据模型
│   │   └── schemas.py       # Pydantic模型定义
│   ├── agent/               # Agent核心逻辑
│   │   ├── state.py         # Agent状态定义
│   │   ├── model.py         # 通义模型集成
│   │   ├── graph.py         # Agent图定义
│   │   ├── memory.py        # 内存管理
│   │   └── tools/           # 工具管理
│   │       ├── mcp_tools.py # MCP工具集成
│   │       ├── custom_tools.py # 自定义工具
│   │       └── __init__.py  # 工具管理器
│   └── api/
│       ├── __init__.py      # API路由整合
│       └── deps.py          # 依赖项
├── frontend/                # 前端项目
│   ├── public/              # 静态资源
│   ├── src/                 # 源代码
│   │   ├── views/           # 页面组件
│   │   ├── router/          # 路由配置
│   │   ├── App.vue          # 根组件
│   │   └── main.js          # 入口文件
│   ├── package.json         # 项目依赖
│   └── vue.config.js        # Vue配置
├── init_db.py               # 数据库初始化脚本
├── requirements.txt         # 项目依赖
├── DESIGN.md               # 设计文档
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
- `TONGYI_API_KEY`: 通义模型API密钥
- `TONGYI_MODEL_NAME`: 通义模型名称（默认：qwen-plus）
- `DEBUG`: 调试模式（默认：False）
- `LOG_LEVEL`: 日志级别（默认：INFO）

### 3. 初始化数据库

```bash
python init_db.py
```

### 4. 启动后端服务

```bash
python app/main.py
```

或者使用uvicorn：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. 安装前端依赖

```bash
cd frontend
npm install
```

### 6. 启动前端开发服务器

```bash
npm run serve
```

### 7. 访问应用

- 前端界面: http://localhost:8080
- API文档: http://localhost:8000/docs

## API接口

### 会话管理
- `POST /api/sessions` - 创建新会话
- `GET /api/sessions/{session_id}` - 获取会话信息
- `DELETE /api/sessions/{session_id}` - 删除会话
- `GET /api/sessions` - 列出当前用户的所有会话

### Agent执行
- `POST /api/sessions/{session_id}/execute` - 执行Agent任务
- `POST /api/sessions/{session_id}/chat` - 与Agent聊天（支持连续对话）
- `GET /api/sessions/{session_id}/messages` - 获取对话历史
- `DELETE /api/sessions/{session_id}/messages` - 清空对话历史

### 工具管理
- `GET /api/tools` - 列出所有可用工具
- `PUT /api/tools/{tool_id}/approval` - 设置工具审批配置

### 审批管理
- `POST /api/approvals` - 请求工具执行审批
- `GET /api/approvals` - 列出所有待审批项
- `POST /api/approvals/{approval_id}/approve` - 批准工具执行
- `POST /api/approvals/{approval_id}/reject` - 拒绝工具执行

### 用户管理
- `POST /api/users` - 用户注册
- `POST /api/users/login` - 用户登录
- `GET /api/users/profile` - 获取用户信息
- `PUT /api/users/profile` - 更新用户信息

## 前端功能

### 聊天界面
- 实时与Agent对话
- 显示对话历史
- 支持多轮对话

### 工具管理
- 查看可用工具列表
- 配置工具审批规则

### 审批管理
- 查看待审批请求
- 批准或拒绝工具执行

## 工具审批机制

系统支持灵活的工具审批机制，可以针对不同用户和工具进行个性化配置：

1. **默认配置**: 当用户没有特定配置时，使用默认审批规则
2. **用户特定配置**: 每个用户可以为特定工具设置独立的审批规则
3. **审批类型**:
   - 自动执行: 工具无需审批直接执行
   - 人工审批: 工具执行前需要人工审批

## 数据模型

### 用户表 (users)
存储系统用户信息

### 用户会话关系表 (user_sessions)
存储用户会话信息

### 工具审批配置表 (tool_approval_config)
存储工具审批配置，支持默认配置和用户特定配置

## 许可证

[MIT License](LICENSE)