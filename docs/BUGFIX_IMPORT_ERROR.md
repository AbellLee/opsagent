# 导入错误修复

## 问题描述

启动后端服务时出现以下错误：

```
ModuleNotFoundError: No module named 'app.core.database'
```

## 错误原因

在第三阶段修改 `app/api/routes/dify.py` 时，错误地使用了不存在的导入：

```python
from app.core.database import get_db  # ❌ 错误
```

## 解决方案

修改为使用正确的导入路径：

```python
from app.api.deps import get_db  # ✅ 正确
```

## 修改的文件

- `app/api/routes/dify.py` - 第 8 行

## 验证

服务器成功启动：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started server process [27164]
INFO:     Waiting for application startup.
2025-11-08 19:33:27,490 - opsagent - INFO - 正在初始化模型...
2025-11-08 19:33:27,781 - opsagent - INFO - LLM初始化完成
2025-11-08 19:33:27,781 - opsagent - INFO - Graph将在需要时动态创建
INFO:     Application startup complete.
```

## 相关说明

项目中有两个 `get_db()` 函数：

1. **`app.api.deps.get_db()`** - 返回 psycopg2 连接（原有代码）
2. **`app.db.session.get_db_sqlalchemy()`** - 返回 SQLAlchemy 会话（新增）

为了保持向后兼容，`app.db.session` 中设置了别名：

```python
get_db = get_db_psycopg2  # 默认使用 psycopg2
get_db_orm = get_db_sqlalchemy  # 新功能使用 ORM
```

在现有路由中应该继续使用 `app.api.deps.get_db()`，只有新的 LLM 配置相关功能才使用 `get_db_orm()`。

