# OpsAgent 代码改进快速参考

本文档提供改进后的代码使用快速参考。

---

## 📚 Logger使用

### 基本用法

```python
# 1. 导入
from app.core.logger import get_logger

# 2. 创建模块级logger（推荐）
logger = get_logger("agent.graph")  # 自动添加"opsagent."前缀

# 3. 使用
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息", exc_info=True)  # 推荐：包含堆栈信息
logger.critical("严重错误", exc_info=True)
```

### 模块命名规范

```python
# 按文件路径命名
app/agent/graph.py          → get_logger("agent.graph")
app/services/agent/handlers.py → get_logger("services.agent.handlers")
app/api/routes/agent.py     → get_logger("api.routes.agent")
```

### 配置文件日志

```bash
# .env
LOG_LEVEL=INFO
LOG_FILE=/var/log/opsagent/app.log  # 可选，不设置则只输出到控制台
```

---

## 🔤 类型注解规范

### 函数签名

```python
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage

# ✅ 推荐：完整的类型注解
async def my_function(
    session_id: UUID,
    message: str,
    tools: Optional[List[BaseTool]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """函数说明"""
    pass

# ❌ 避免：缺少类型注解
async def my_function(session_id, message, tools=None, config=None):
    pass
```

### 常用类型

```python
# 基础类型
str, int, float, bool

# 容器类型
List[str]                    # 字符串列表
Dict[str, Any]              # 字典
Tuple[str, int]             # 元组
Optional[str]               # 可选字符串（可以是None）

# LangChain类型
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

# LangGraph类型
from langgraph.store.base import BaseStore
```

---

## ⚠️ 错误处理规范

### 基本模式

```python
# ✅ 推荐：具体的异常类型 + exc_info
from psycopg2 import DatabaseError, OperationalError

try:
    # 数据库操作
    result = db.execute(query)
except (DatabaseError, OperationalError) as e:
    logger.error(f"数据库操作失败: {e}", exc_info=True)
    # 处理错误
except Exception as e:
    logger.error(f"未知错误: {e}", exc_info=True)
    raise  # 重新抛出未知错误
```

### 资源管理

```python
# ✅ 推荐：明确的资源管理
conn = None
try:
    conn = psycopg2.connect(...)
    # 操作
finally:
    if conn is not None:
        conn.close()

# 🌟 更好：使用上下文管理器
async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer:
    # 操作
    # 自动清理
```

### 常见异常类型

```python
# 数据库相关
from psycopg2 import DatabaseError, OperationalError, IntegrityError

# LLM相关
from app.core.llm import LLMInitializationError

# 标准异常
ValueError          # 值错误
TypeError           # 类型错误
KeyError            # 键不存在
FileNotFoundError   # 文件不存在
```

---

## 📝 文档字符串模板

### 完整模板

```python
def function_name(
    param1: str,
    param2: Optional[int] = None
) -> Dict[str, Any]:
    """简短的一句话描述函数功能
    
    更详细的描述（可选，如果需要解释复杂逻辑）
    
    Args:
        param1: 参数1的说明
        param2: 参数2的说明，默认为None
    
    Returns:
        返回值的说明，包括结构：
        - key1: 字段1的说明
        - key2: 字段2的说明
    
    Raises:
        ValueError: 什么情况下抛出ValueError
        DatabaseError: 什么情况下抛出DatabaseError
    
    Example:
        >>> result = function_name("test", 42)
        >>> print(result["key1"])
        "value"
    
    Note:
        重要的注意事项或使用提示
    """
    pass
```

### 简化模板（简单函数）

```python
def simple_function(param: str) -> str:
    """简短的一句话描述
    
    Args:
        param: 参数说明
    
    Returns:
        返回值说明
    """
    pass
```

---

## 🎨 代码风格检查清单

### 提交前检查

- [ ] 所有函数都有类型注解
- [ ] 所有函数都有文档字符串
- [ ] 使用模块级logger（`get_logger()`）
- [ ] 错误日志包含`exc_info=True`
- [ ] 使用具体的异常类型
- [ ] 资源正确释放（使用finally或上下文管理器）

### 代码审查要点

```python
# ✅ 好的代码示例
from app.core.logger import get_logger
from typing import Optional, Dict, Any

logger = get_logger("services.example")

async def process_data(
    data: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """处理数据
    
    Args:
        data: 输入数据
        config: 可选配置
    
    Returns:
        处理结果字典
    
    Raises:
        ValueError: 当数据格式无效时
    """
    try:
        logger.info(f"开始处理数据: {len(data)} 字节")
        result = do_something(data)
        logger.info("数据处理成功")
        return {"status": "success", "result": result}
    except ValueError as e:
        logger.error(f"数据格式无效: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"处理失败: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}
```

---

## 🔧 常见问题

### Q1: 什么时候使用exc_info=True？

**A**: 在记录错误和警告时都应该使用：

```python
logger.error("错误信息", exc_info=True)   # ✅ 推荐
logger.warning("警告信息", exc_info=True) # ✅ 推荐（如果在except块中）
logger.info("普通信息")                   # ❌ 不需要
```

### Q2: 如何选择异常类型？

**A**: 从具体到一般：

```python
try:
    # 操作
except SpecificError as e:      # 1. 最具体的异常
    # 处理
except BroadError as e:         # 2. 较宽泛的异常
    # 处理
except Exception as e:          # 3. 最后的兜底
    # 处理或重新抛出
```

### Q3: 文档字符串必须包含所有部分吗？

**A**: 不是，根据函数复杂度选择：

- **简单函数**: 只需要简短描述 + Args + Returns
- **复杂函数**: 添加 Raises + Example + Note
- **公共API**: 建议包含所有部分

### Q4: 如何命名logger？

**A**: 使用文件路径（去掉app/和.py）：

```python
# 文件: app/services/agent/handlers.py
logger = get_logger("services.agent.handlers")

# 文件: app/agent/graph.py
logger = get_logger("agent.graph")
```

---

## 📖 参考资源

### 内部文档

- [完整改进分析](./CODE_STYLE_IMPROVEMENTS.md)
- [改进总结](./IMPROVEMENTS_SUMMARY.md)
- [与OpenAgent对比](./COMPARISON_WITH_OPENAGENT.md)

### Python最佳实践

- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [PEP 257 - Docstring Conventions](https://peps.python.org/pep-0257/)
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)

---

## ✨ 快速示例

### 完整的函数示例

```python
from typing import Optional, Dict, Any, List
from uuid import UUID
from app.core.logger import get_logger
from langchain_core.tools import BaseTool

logger = get_logger("services.example")

async def execute_task(
    session_id: UUID,
    message: str,
    tools: Optional[List[BaseTool]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """执行任务的核心业务逻辑
    
    Args:
        session_id: 会话ID
        message: 用户消息
        tools: 可用工具列表，默认为None
        config: 任务配置，默认为None
    
    Returns:
        包含以下字段的字典：
        - session_id: 会话ID
        - response: 响应内容
        - status: 执行状态 ("success" | "error")
    
    Raises:
        ValueError: 当message为空时
    
    Example:
        >>> result = await execute_task(
        ...     session_id=UUID("..."),
        ...     message="Hello"
        ... )
        >>> print(result["status"])
        "success"
    """
    if not message or not message.strip():
        raise ValueError("消息不能为空")
    
    try:
        logger.info(f"开始执行任务: session_id={session_id}")
        
        # 执行逻辑
        response = await process_message(message, tools, config)
        
        logger.info(f"任务执行成功: session_id={session_id}")
        return {
            "session_id": session_id,
            "response": response,
            "status": "success"
        }
    except ValueError as e:
        logger.error(f"参数错误: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"任务执行失败: {e}", exc_info=True)
        return {
            "session_id": session_id,
            "response": f"执行失败: {str(e)}",
            "status": "error"
        }
```

---

**记住**: 好的代码不仅能运行，还要易读、易维护、易调试！🚀

