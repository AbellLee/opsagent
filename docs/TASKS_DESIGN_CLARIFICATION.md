# Tasks 设计澄清与修复

## 📅 日期
2025-11-09

## 🎯 问题背景

在尝试实现 LangGraph 节点自动追踪功能时，混淆了两个不同的概念：

1. **原有的 tasks 设计**：Agent 的待办事项列表（由 Agent 主动管理）
2. **误实现的 task_sync**：LangGraph 节点执行追踪（自动记录节点执行）

这导致了设计混乱和功能冲突。

---

## 📋 原有 Tasks 设计（正确的）

### 1. 设计意图

**tasks 是 LangChain 工具**，供 Agent 主动调用来管理自己的待办事项列表。

### 2. 核心工具

#### `add_tasks` 工具
```python
@tool
def add_tasks(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """添加一个或多个新任务到任务列表中"""
```

**用途**：Agent 创建新的待办任务

**参数**：
- `content`: 任务内容
- `status`: 任务状态（PENDING, IN_PROGRESS, COMPLETE, CANCELLED, ERROR）
- `parent_task_id`: 父任务ID（可选，用于创建子任务）

#### `update_tasks` 工具
```python
@tool
def update_tasks(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """更新一个或多个任务的属性（状态、内容等）"""
```

**用途**：Agent 更新现有任务的状态或内容

**参数**：
- `id`: 要更新的任务ID（必需）
- `content`: 新的任务内容（可选）
- `status`: 新的任务状态（可选）

#### `get_tasks` 工具
```python
@tool
def get_tasks(status: str = None) -> Dict[str, Any]:
    """获取任务列表"""
```

**用途**：Agent 查询当前的任务列表

**参数**：
- `status`: 任务状态筛选器（可选）

### 3. 数据库表结构

```sql
CREATE TABLE tasks (
    id VARCHAR(8) PRIMARY KEY,              -- 8位短ID
    user_id UUID REFERENCES users(user_id),
    session_id UUID,
    content TEXT NOT NULL,                  -- 任务描述
    status VARCHAR(20) NOT NULL,            -- 任务状态
    parent_task_id VARCHAR(8),              -- 父任务ID（支持层级关系）
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 4. 使用场景

**场景 1：Agent 规划复杂任务**

用户："帮我部署一个新的微服务"

Agent 思考：
1. 调用 `add_tasks` 创建主任务："部署微服务"
2. 调用 `add_tasks` 创建子任务：
   - "检查环境配置"
   - "构建 Docker 镜像"
   - "部署到 Kubernetes"
   - "验证服务健康"
3. 逐步执行每个子任务
4. 调用 `update_tasks` 更新任务状态

**场景 2：Agent 跟踪进度**

用户："当前任务进度如何？"

Agent：
1. 调用 `get_tasks` 获取所有任务
2. 分析任务状态
3. 向用户报告进度

### 5. 前端展示

前端通过 WebSocket 实时接收任务更新，展示为：

```
📋 任务列表
├─ [✓] 部署微服务
│   ├─ [✓] 检查环境配置
│   ├─ [/] 构建 Docker 镜像
│   ├─ [ ] 部署到 Kubernetes
│   └─ [ ] 验证服务健康
```

---

## ❌ 误实现的 task_sync（已移除）

### 1. 错误的设计

我之前实现的 `task_sync` 试图：
- 自动追踪 LangGraph 节点执行
- 使用装饰器 `@with_task_tracking` 包装节点
- 将节点执行记录写入同一个 `tasks` 表

### 2. 导致的问题

1. **概念混淆**：
   - Agent 主动创建的任务（待办事项）
   - 系统自动记录的节点执行（调试信息）
   - 两者混在同一个表中

2. **前端展示混乱**：
   ```
   📋 任务列表
   ├─ [✓] 部署微服务          ← Agent 创建的任务
   ├─ [✓] 执行节点: call_model  ← 系统自动记录（不应该显示）
   ├─ [✓] 执行节点: tools       ← 系统自动记录（不应该显示）
   │   ├─ [✓] 检查环境配置      ← Agent 创建的子任务
   │   └─ [✓] 执行节点: call_model ← 系统自动记录（不应该显示）
   ```

3. **数据库错误**：
   - `custom_tools.py` 中的 `_check_user_exists` 使用了错误的列名 `id` 而不是 `user_id`
   - 导致 `column "id" does not exist` 错误

---

## ✅ 修复措施

### 1. 移除自动追踪功能

删除了以下文件：
- `app/agent/task_sync.py`
- `app/agent/task_context.py`
- `scripts/test_task_sync.py`
- `scripts/simple_error_test.py`
- `scripts/test_error_detection.py`
- `docs/LANGGRAPH_TASK_SYNC.md`
- `docs/TASK_SYNC_IMPLEMENTATION.md`
- `docs/QUICK_START_TASK_SYNC.md`
- `docs/TASK_SYNC_FIXES.md`
- `CHANGELOG_TASK_SYNC.md`
- `examples/task_sync_example.py`
- `tests/test_task_sync.py`

### 2. 恢复原有代码

**`app/agent/nodes.py`**：
```python
# 移除前
from app.agent.task_sync import with_task_tracking, get_task_sync_manager

@with_task_tracking(auto_complete=True)
async def call_model(...):
    ...

# 移除后
async def call_model(...):
    ...
```

**`app/agent/graph.py`**：
```python
# 移除前
from app.agent.task_sync import with_task_tracking

def create_tracked_tool_node(tools):
    tool_node = ToolNode(tools)
    
    @with_task_tracking(auto_complete=True)
    async def tracked_tool_node(state, config):
        return await tool_node.ainvoke(state, config)
    
    return tracked_tool_node

tool_node = create_tracked_tool_node(available_tools)

# 移除后
tool_node = ToolNode(available_tools)
```

### 3. 修复数据库查询错误

**`app/agent/tools/custom_tools.py`**：
```python
# 修复前
def _check_user_exists(cursor, user_id: str) -> bool:
    cursor.execute("SELECT 1 FROM users WHERE id = %s", (user_id,))  # ❌ 错误
    return cursor.fetchone() is not None

# 修复后
def _check_user_exists(cursor, user_id: str) -> bool:
    cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))  # ✅ 正确
    return cursor.fetchone() is not None
```

**原因**：`users` 表的主键是 `user_id`，不是 `id`。

---

## 🎯 正确的使用方式

### Agent 如何使用 tasks 工具

**示例对话：**

```
用户: 帮我部署一个新的微服务到生产环境

Agent: 好的，我来为你规划部署任务。

[Agent 调用 add_tasks 工具]
{
  "tasks": [
    {
      "content": "部署微服务到生产环境",
      "status": "IN_PROGRESS"
    }
  ]
}

[Agent 调用 add_tasks 工具创建子任务]
{
  "tasks": [
    {
      "content": "1. 检查生产环境配置",
      "status": "PENDING",
      "parent_task_id": "a1b2c3d4"
    },
    {
      "content": "2. 构建 Docker 镜像",
      "status": "PENDING",
      "parent_task_id": "a1b2c3d4"
    },
    {
      "content": "3. 推送镜像到仓库",
      "status": "PENDING",
      "parent_task_id": "a1b2c3d4"
    },
    {
      "content": "4. 部署到 Kubernetes",
      "status": "PENDING",
      "parent_task_id": "a1b2c3d4"
    },
    {
      "content": "5. 验证服务健康",
      "status": "PENDING",
      "parent_task_id": "a1b2c3d4"
    }
  ]
}

Agent: 我已经为你创建了部署计划，包含 5 个步骤。现在开始执行...

[Agent 执行第一个任务]
[Agent 调用 update_tasks 更新状态]
{
  "tasks": [
    {
      "id": "e5f6g7h8",
      "status": "COMPLETE"
    }
  ]
}

Agent: ✓ 已完成环境配置检查，现在开始构建镜像...
```

---

## 📊 总结

### 关键要点

1. **tasks 是 Agent 的工具**，不是系统的调试工具
2. **Agent 主动管理任务**，而不是系统自动记录
3. **tasks 表只存储 Agent 的待办事项**，不存储节点执行记录
4. **前端展示的是 Agent 的任务规划**，不是系统内部执行流程

### 如果需要节点执行追踪

如果将来需要追踪 LangGraph 节点执行，应该：

1. **创建独立的表**：`node_executions` 或 `execution_logs`
2. **不与 tasks 混合**：保持两个功能独立
3. **不在前端任务列表中显示**：可以在单独的调试面板中查看
4. **考虑使用 LangGraph 的内置功能**：
   - LangGraph 的 checkpoint 系统已经记录了所有状态变化
   - 可以通过 checkpoint 查询执行历史

---

**状态：** ✅ 已修复并恢复原有设计  
**最后更新：** 2025-11-09

