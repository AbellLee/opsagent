# 修复 ChatCompletionResponse 验证错误 · backend · 2025-10-24
> 相关路径：app/models/schemas.py, app/services/agent/handlers.py

## 背景 / 目标
- 需求/问题：
  在与AI助手对话时，后端出现 Pydantic 验证错误：`Input should be a valid string`。这是因为在 [ChatCompletionResponse](file:///D:/python/opsagent/app/models/schemas.py#L47-L54) 模型中，[response](file:///D:/python/opsagent/app/models/schemas.py#L50-L50) 字段被定义为字符串类型，但实际传入的是包含消息详细信息的字典对象。
- 约束/边界：
  需要保持 API 响应格式的一致性，同时确保数据验证通过。

## 方案摘要
- 核心思路：
  1. 在 [handle_blocking_chat](file:///D:/python/opsagent/app/services/agent/handlers.py#L62-L119) 函数中添加逻辑，将字典格式的消息内容转换为字符串格式
  2. 对于包含多种类型内容（如文本和工具调用）的消息，提取其中的文本内容进行返回
  3. 保持模型定义不变，仅调整数据处理逻辑
- 影响面：
  - 代码：[app/services/agent/handlers.py](file:///D:/python/opsagent/app/services/agent/handlers.py)
  - 配置：无
  - 脚本：无

## 变更清单（按文件分组）
- `app/services/agent/handlers.py`
  - 变更点：修改 [handle_blocking_chat](file:///D:/python/opsagent/app/services/agent/handlers.py#L62-L119) 函数中对响应内容的处理逻辑
  - 片段/伪代码/要点：
    ```python
    # 将消息内容转换为字符串格式
    if isinstance(response_message, dict):
        # 如果是字典，提取content字段或转换为JSON字符串
        response_content = response_message.get("content", "")
        if isinstance(response_content, list):
            # 如果content是列表，提取其中的文本内容
            text_contents = [item.get("content", "") for item in response_content if item.get("type") == "text"]
            response_content = "\n".join(text_contents)
        elif not isinstance(response_content, str):
            # 如果content不是字符串，转换为JSON字符串
            import json
            response_content = json.dumps(response_content, ensure_ascii=False)
    else:
        # 如果不是字典，直接转换为字符串
        response_content = str(response_message)

    return ChatCompletionResponse(
        session_id=str(session_id),
        response=response_content,  # 返回字符串格式的响应
        status="success",
        created_at=time.time(),
        model="tongyi"
    )
    ```

## 指令与运行
```bash
# 启动开发服务器
python -m uvicorn app.main:app --reload

# 运行测试
python -m pytest
```