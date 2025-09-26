from typing import Type, Dict, Any
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from app.core.logger import logger

# 自定义工具输入模型示例
class CalculatorInput(BaseModel):
    expression: str = Field(description="数学表达式，例如: '2 + 3 * 4'")

class CalculatorTool(BaseTool):
    name: str = "calculator"
    description: str = "执行数学计算"
    args_schema: Type[BaseModel] = CalculatorInput

    def _run(self, expression: str) -> Dict[str, Any]:
        try:
            # 安全地计算数学表达式
            # 注意：在生产环境中应该使用更安全的表达式解析器
            allowed_chars = set('0123456789+-*/(). ')
            if not all(c in allowed_chars for c in expression):
                raise ValueError("表达式包含非法字符")
            
            result = eval(expression)  # 注意：eval在生产环境中应谨慎使用
            return {
                "expression": expression,
                "result": result
            }
        except Exception as e:
            logger.error(f"计算表达式 '{expression}' 失败: {e}")
            return {
                "error": str(e),
                "expression": expression
            }

# 自定义工具输入模型示例
class WebSearchInput(BaseModel):
    query: str = Field(description="搜索关键词")

class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = "执行网络搜索"
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str) -> Dict[str, Any]:
        try:
            # 这里应该实现真实的网络搜索逻辑
            # 目前返回占位符响应
            logger.info(f"执行网络搜索: {query}")
            return {
                "query": query,
                "results": [
                    {"title": "搜索结果1", "url": "http://example.com/1", "snippet": "这是搜索结果1的摘要"},
                    {"title": "搜索结果2", "url": "http://example.com/2", "snippet": "这是搜索结果2的摘要"}
                ]
            }
        except Exception as e:
            logger.error(f"网络搜索 '{query}' 失败: {e}")
            return {
                "error": str(e),
                "query": query
            }

# 注册自定义工具
def get_custom_tools() -> list:
    """获取所有自定义工具"""
    return [
        CalculatorTool(),
        WebSearchTool()
    ]