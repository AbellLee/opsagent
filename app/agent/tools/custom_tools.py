from typing import Dict, Any
from langchain_core.tools import tool
from app.core.logger import logger

@tool
def calculator(expression: str) -> dict:
    """执行数学计算

    Args:
        expression: 数学表达式，例如: '2 + 3 * 4'
    """
    try:
        # 安全地计算数学表达式
        # 注意：在生产环境中应该使用更安全的表达式解析器
        allowed_chars = set('0123456789+-*/(). ')
        if not all(c in allowed_chars for c in expression):
            raise ValueError("表达式包含非法字符")

        result = eval(expression)  # 注意：eval在生产环境中应谨慎使用
        logger.info(f"计算表达式 '{expression}' = {result}")
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

@tool
def web_search(query: str) -> dict:
    """执行网络搜索

    Args:
        query: 搜索关键词
    """
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
        calculator,
        web_search
    ]