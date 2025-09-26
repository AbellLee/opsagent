# Agent系统设计方案

基于langgraph、fastapi和postgresql构建支持记忆、MCP工具和自定义工具功能的Agent系统

## 1. 系统概述

本方案旨在设计一个基于langgraph、fastapi和postgresql的Agent系统，该系统具备以下核心功能：
- 支持短期记忆管理（通过PostgreSQL检查点）
- 集成MCP工具支持
- 支持自定义工具扩展
- 提供RESTful API服务
- 实现工具执行审批机制

## 2. 技术栈

- **核心框架**: langgraph (用于构建Agent逻辑流)
- **Web框架**: fastapi (用于提供API服务)
- **数据库**: postgresql (用于持久化状态和检查点)
- **AI模型**: 通义语言模型 (核心AI能力)
- **内存管理**: langgraph-checkpoint-postgres (用于Agent状态持久化)
- **MCP支持**: 待定(根据实际MCP规范集成)

## 3. 系统架构设计

### 3.1 整体架构

```
┌─────────────────┐
│   FastAPI服务层  │ ← REST API接口
└─────────┬───────┘
          │
┌─────────▼───────┐
│   Agent管理层   │ ← langgraph实现的Agent逻辑
└─────────┬───────┘
          │
┌─────────▼───────┐
│   工具执行层     │ ← MCP工具 + 自定义工具
└─────────┬───────┘
          │
┌─────────▼───────┐
│   记忆管理层     │ ← PostgreSQL检查点
└─────────────────┘
```

### 3.2 核心组件

#### 3.2.1 Agent状态管理
- 使用PostgreSQL作为检查点存储
- 实现短期记忆功能，支持多轮对话
- 会话隔离，通过thread_id区分不同用户会话

#### 3.2.2 工具系统
- 支持MCP标准工具注册和执行
- 支持自定义工具动态加载
- 工具沙箱执行环境（可选安全特性）
- 工具执行审批机制：
  - 可配置工具是否需要人工审核
  - 提供审批接口供管理员审核工具执行请求
  - 支持自动执行和人工审核两种模式
  - 支持不同用户的个性化审批配置

#### 3.2.3 AI模型集成
- 集成通义语言模型作为核心AI能力
- 支持模型调用和响应处理
- 实现与langgraph的无缝集成

#### 3.2.4 API服务层
- 提供WebSocket和HTTP接口
- 会话管理API
- Agent执行控制API
- 工具管理API
- 工具审批管理API

## 4. 数据模型设计

### 4.1 用户表 (users)
| 字段名 | 类型 | 描述 |
|--------|------|------|
| user_id | UUID | 用户唯一标识 |
| username | STRING | 用户名 |
| email | STRING | 邮箱地址 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 4.2 用户会话关系表 (user_sessions)
| 字段名 | 类型 | 描述 |
|--------|------|------|
| session_id | UUID | 会话唯一标识 |
| user_id | UUID | 关联的用户ID |
| created_at | TIMESTAMP | 会话创建时间 |
| expires_at | TIMESTAMP | 会话过期时间 |

### 4.3 工具审批配置表 (tool_approval_config)
| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | UUID | 配置唯一标识 |
| user_id | UUID | 用户ID（NULL表示默认配置） |
| tool_id | UUID | 工具唯一标识 |
| tool_name | STRING | 工具名称 |
| auto_execute | BOOLEAN | 是否自动执行 |
| approval_required | BOOLEAN | 是否需要人工审核 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

> 注意：当user_id为NULL时，表示这是默认配置，适用于所有未单独配置的用户。每个用户可以有针对特定工具的独立配置，user_id和tool_id构成联合唯一索引。

> 注意：其他的数据表（如检查点相关的表）将由langgraph自动初始化和管理。

## 5. API接口设计

### 5.1 会话管理接口
- `POST /api/sessions` - 创建新会话
- `GET /api/sessions/{session_id}` - 获取会话信息
- `DELETE /api/sessions/{session_id}` - 删除会话
- `GET /api/sessions` - 列出当前用户的所有会话

### 5.2 Agent执行接口
- `POST /api/sessions/{session_id}/execute` - 执行Agent任务
- `GET /api/sessions/{session_id}/messages` - 获取对话历史
- `DELETE /api/sessions/{session_id}/messages` - 清空对话历史

### 5.3 工具管理接口
- `GET /api/tools` - 列出所有可用工具
- `GET /api/tools/{tool_id}` - 获取特定工具详情
- `PUT /api/tools/{tool_id}/approval` - 设置工具审批配置
- `GET /api/tools/pending-approvals` - 获取待审批工具列表
- `POST /api/tools/approvals/{approval_id}/approve` - 批准工具执行
- `POST /api/tools/approvals/{approval_id}/reject` - 拒绝工具执行

### 5.4 审批管理接口
- `POST /api/approvals` - 请求工具执行审批
- `GET /api/approvals` - 列出所有待审批项
- `POST /api/approvals/{approval_id}/approve` - 批准工具执行
- `POST /api/approvals/{approval_id}/reject` - 拒绝工具执行

### 5.5 用户管理接口
- `POST /api/users` - 用户注册
- `POST /api/users/login` - 用户登录
- `GET /api/users/profile` - 获取用户信息
- `PUT /api/users/profile` - 更新用户信息

## 6. 项目结构

```
opsagent/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── sessions.py  # 会话管理路由
│   │   │   ├── tools.py     # 工具管理路由
│   │   │   ├── users.py     # 用户管理路由
│   │   │   ├── agent.py     # Agent执行路由
│   │   │   └── approvals.py # 审批管理路由
│   │   └── deps.py          # 依赖项
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # 配置管理
│   │   └── logger.py        # 日志配置
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py         # langgraph定义
│   │   ├── state.py         # 状态定义
│   │   ├── model.py         # 通义模型集成
│   │   ├── memory.py        # 内存管理
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── mcp_tools.py # MCP工具集成
│   │       └── custom_tools.py # 自定义工具
│   └── models/
│       ├── __init__.py
│       └── schemas.py       # 数据模型定义
├── init_db.py               # 数据库初始化脚本
├── requirements.txt
└── README.md
```

## 7. 关键实现细节

### 7.1 内存管理实现
使用PostgreSQL作为检查点后端，确保Agent状态持久化：

```python
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgresql://user:password@localhost:5432/agentdb"
checkpointer = PostgresSaver.from_conn_string(DB_URI)
# 首次使用需要初始化表结构
# checkpointer.setup()
```

### 7.2 Agent图构建
使用StateGraph构建Agent逻辑流，支持工具调用和状态管理。

### 7.3 FastAPI集成
通过FastAPI提供RESTful接口，将会话ID映射到langgraph的thread_id。

### 7.4 工具审批机制
实现灵活的工具审批机制，支持默认配置和用户特定配置：
1. 工具执行前检查审批配置
2. 根据配置决定是否需要人工审批
3. 提供API接口管理审批请求
4. 支持批准或拒绝工具执行

## 8. 环境变量配置
- DATABASE_URL: PostgreSQL连接字符串
- API_KEY: API访问密钥
- LOG_LEVEL: 日志级别
- TONGYI_API_KEY: 通义模型API密钥
- TONGYI_MODEL_NAME: 通义模型名称

## 9. 安全考虑

- API访问认证和授权
- 工具执行沙箱隔离
- 敏感信息加密存储
- 输入验证和过滤

## 10. 性能优化

- 连接池管理
- 数据库索引优化
- 异步处理支持
- 缓存机制