# LLM平台集成重构 · backend · 2025-10-24
> 相关路径：app/core/llm.py、app/core/config.py

## 背景 / 目标
- 需求/问题：
  - 原有的LLM集成方式仅支持有限的平台，且使用统一的ChatOpenAI接口，无法充分利用各平台的特性和功能
  - 需要通过Langchain官方包兼容更多平台：Ollama、OpenAI、vLLM、DeepSeek、通义千问
  - 提高代码的可维护性和扩展性，便于后续添加新的LLM平台

- 约束/边界：
  - 保持与现有代码的兼容性
  - 不改变对外接口
  - 支持配置文件方式配置各平台参数

## 方案摘要
- 核心思路（1~3 条）：
  1. 为每个LLM平台使用Langchain官方提供的特定集成包
  2. 扩展MODEL_CONFIGS配置，增加provider_package字段标识各平台使用的包
  3. 在initialize_llm函数中根据平台类型动态导入并实例化对应的类

- 影响面（代码/配置/脚本）：
  - 核心LLM初始化逻辑(app/core/llm.py)
  - 配置管理(app/core/config.py)
  - 环境变量配置支持

## 变更清单（按文件分组）
- `app/core/llm.py`
  - 变更点：
    1. 扩展LLMConfig类，增加provider_package字段
    2. 更新MODEL_CONFIGS，添加对Ollama、DeepSeek、vLLM等平台的支持
    3. 修改initialize_llm函数，根据平台类型动态导入并实例化对应的类
    4. 更新_get_api_key和_get_base_url函数，支持各平台特定的处理逻辑
  - 片段/伪代码/要点：
    ```python
    # 添加新的平台配置
    "deepseek": LLMConfig(
        base_url="https://api.deepseek.com/v1",
        api_key_env="DEEPSEEK_API_KEY",
        default_chat_model="deepseek-chat",
        default_embedding_model=None,
        provider_package="langchain_deepseek"
    ),
    # 动态导入并实例化
    elif llm_type == "deepseek":
        from langchain_deepseek import ChatDeepSeek
        llm = ChatDeepSeek(...)
    ```

- `app/core/config.py`
  - 变更点：
    1. 添加各平台特定的API密钥环境变量配置项
  - 片段/伪代码/要点：
    ```python
    # 添加平台特定的API密钥配置
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    deepseek_api_key: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    dashscope_api_key: Optional[str] = os.getenv("DASHSCOPE_API_KEY")
    ```

## 指令与运行
```bash
# 安装所需的依赖包
pip install langchain-openai langchain-ollama langchain-deepseek

# 配置环境变量(示例)
export LLM_TYPE=ollama
export LLM_MODEL=llama3

# 运行应用
python app/main.py
```