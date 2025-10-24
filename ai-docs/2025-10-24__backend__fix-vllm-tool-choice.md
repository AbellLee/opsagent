# 修复vLLM工具选择错误 · backend · 2025-10-24
> 相关路径：app/agent/graph.py、app/core/llm.py

## 背景 / 目标
- 需求/问题：
  - 当使用vLLM作为后端LLM时，出现错误："auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set
  - 这是因为vLLM需要在服务器端设置特定参数才能支持自动工具选择功能
  - 错误导致模型调用失败，影响了Agent的功能
  - 后续还出现了JSON格式错误，表明工具调用参数可能存在问题

- 约束/边界：
  - 不能要求用户修改vLLM服务器配置
  - 需要在代码层面解决此问题
  - 保持对其他LLM平台的兼容性

## 方案摘要
- 核心思路（1~3 条）：
  1. 检测当前使用的LLM类型是否为vLLM
  2. 对于vLLM，暂时不使用工具以避免JSON格式问题
  3. 对其他LLM平台保持原有处理方式
  4. 增加异常处理，确保即使工具绑定失败也能继续运行

- 影响面（代码/配置/脚本）：
  - Agent图构建逻辑(app/agent/graph.py)

## 变更清单（按文件分组）
- `app/agent/graph.py`
  - 变更点：在绑定工具到模型时，针对vLLM不使用工具，对其他模型保持原有处理方式
  - 片段/伪代码/要点：
    ```python
    # 针对vLLM的特殊处理，避免使用"auto"工具选择模式
    # 因为vLLM需要额外的服务器端配置才能支持"auto"模式
    from app.core.config import settings
    llm_type = getattr(settings, 'llm_type', os.getenv("LLM_TYPE", "tongyi"))
    
    # 对于vLLM，暂时不使用工具，因为存在JSON格式问题
    if llm_type == "vllm":
        model_with_tools = llm
        logger.info("使用vLLM，暂时不绑定工具以避免JSON格式问题")
    else:
        try:
            model_with_tools = llm.bind_tools(tools)
            logger.info(f"已绑定 {len(tools)} 个工具到模型")
        except Exception as bind_error:
            logger.warning(f"绑定工具到模型时出错: {bind_error}，将使用无工具的模型")
            model_with_tools = llm
    ```

## 指令与运行
```bash
# 配置环境变量使用vLLM
export LLM_TYPE=vllm
export LLM_MODEL=llama3
export LLM_BASE_URL=http://localhost:8000/v1

# 运行应用
python app/main.py
```