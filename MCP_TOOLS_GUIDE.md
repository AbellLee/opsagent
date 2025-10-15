# MCP工具集成指南

本项目已集成LangGraph官方的MCP（Model Context Protocol）工具支持，允许您连接和使用外部MCP服务器提供的工具。

## 安装依赖

确保已安装必要的依赖包：

```bash
pip install langchain-mcp-adapters mcp
```

## 配置MCP服务器

⚠️ **注意**: 从v2.0开始，MCP服务器配置已迁移到数据库存储，不再使用环境变量。

### 数据库配置方式

使用REST API管理MCP服务器配置：

```bash
# 创建stdio传输的MCP服务器
curl -X POST "http://localhost:8000/mcp-configs/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "math",
    "description": "数学计算服务器",
    "config": {
      "command": "python",
      "args": ["/path/to/your/math_server.py"],
      "transport": "stdio"
    },
    "enabled": true
  }'

# 创建HTTP传输的MCP服务器
curl -X POST "http://localhost:8000/mcp-configs/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "weather",
    "description": "天气查询服务器",
    "config": {
      "url": "http://localhost:8000/mcp",
      "transport": "streamable_http"
    },
    "enabled": true
  }'
```

### MCP配置管理API

#### 查看所有配置
```bash
# 查看所有MCP服务器配置
GET /mcp-configs/

# 只查看启用的配置
GET /mcp-configs/?enabled_only=true
```

#### 查看单个配置
```bash
GET /mcp-configs/{config_id}
```

#### 更新配置
```bash
PUT /mcp-configs/{config_id}
Content-Type: application/json

{
  "description": "更新后的描述",
  "enabled": false
}
```

#### 删除配置
```bash
DELETE /mcp-configs/{config_id}
```

#### 快速启用/禁用
```bash
POST /mcp-configs/{config_id}/toggle
```

### 支持的传输协议

1. **stdio传输**: 适用于本地Python脚本服务器
   - 配置格式:
   ```json
   {
     "command": "python",
     "args": ["/path/to/script.py"],
     "transport": "stdio"
   }
   ```

2. **streamable_http传输**: 适用于HTTP服务器
   - 配置格式:
   ```json
   {
     "url": "http://localhost:8000/mcp",
     "transport": "streamable_http"
   }
   ```

## 创建MCP服务器

### 使用FastMCP创建服务器

```python
from mcp.server.fastmcp import FastMCP

# 创建服务器实例
mcp = FastMCP("YourServerName")

@mcp.tool()
def your_tool(param: str) -> str:
    """工具描述"""
    return f"处理结果: {param}"

if __name__ == "__main__":
    # stdio传输
    mcp.run(transport="stdio")
    
    # 或者HTTP传输
    # mcp.run(transport="streamable-http", port=8000)
```

## 工具管理

### 自动加载

MCP工具会在以下情况下自动加载：
- 首次调用 `tool_manager.get_all_tools()`
- 首次调用 `tool_manager.list_tools()`
- 创建Agent图时

### 手动加载

```python
from app.agent.tools import tool_manager

# 确保MCP工具已加载
await tool_manager.ensure_mcp_tools_loaded()

# 获取所有工具（包括MCP工具）
tools = await tool_manager.get_all_tools()
```

## API使用

### 获取工具列表

```bash
GET /api/tools
```

返回所有可用工具，包括MCP工具和自定义工具。

### 工具类型标识

在工具列表中，每个工具都有 `type` 字段：
- `"MCP"`: MCP服务器提供的工具
- `"Custom"`: 项目内置的自定义工具

## 故障排除

### 常见问题

1. **MCP适配器未安装**
   ```
   WARNING: langchain-mcp-adapters not installed. MCP tools will be disabled.
   ```
   解决方案: `pip install langchain-mcp-adapters`

2. **服务器路径不存在**
   ```
   INFO: 未配置任何MCP服务器
   ```
   解决方案: 检查环境变量中的路径是否正确

3. **服务器连接失败**
   ```
   ERROR: MCP客户端初始化失败
   ```
   解决方案: 检查服务器是否正在运行，端口是否可用

### 调试模式

启用调试日志查看详细信息：

```bash
LOG_LEVEL=DEBUG
```

## 扩展配置

如需添加更多MCP服务器类型，可以修改 `app/agent/tools/mcp_tools.py` 中的 `_load_mcp_servers_config` 方法。

## 安全注意事项

1. 确保MCP服务器来源可信
2. 对于stdio传输，确保Python脚本路径安全
3. 对于HTTP传输，使用HTTPS并验证证书
4. 启用工具审批机制控制工具执行权限
