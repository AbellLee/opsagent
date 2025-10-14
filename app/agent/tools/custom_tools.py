from typing import Dict, Any
from langchain_core.tools import tool
from app.core.logger import logger

@tool
def calculator(expression: str) -> str:
    """执行数学计算

    这个工具可以计算各种数学表达式，包括加减乘除、括号运算等。
    请将完整的数学表达式作为参数传递，不要省略任何部分。

    Args:
        expression (str): 要计算的完整数学表达式。
                         示例: "2 + 3 * 4", "100 + 200", "8783743 + 98423897", "(10 + 5) * 2"
                         支持的运算符: +, -, *, /, (), 数字和空格

    Returns:
        str: 计算结果的字符串表示，包含原表达式和结果
    """
    try:
        # 安全地计算数学表达式
        # 注意：在生产环境中应该使用更安全的表达式解析器
        allowed_chars = set('0123456789+-*/(). ')
        if not all(c in allowed_chars for c in expression):
            raise ValueError("表达式包含非法字符")

        result = eval(expression)  # 注意：eval在生产环境中应谨慎使用
        logger.info(f"计算表达式 '{expression}' = {result}")
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        logger.error(f"计算表达式 '{expression}' 失败: {e}")
        return f"计算失败: {str(e)}"

@tool
def web_search(query: str) -> str:
    """执行网络搜索

    Args:
        query: 搜索关键词

    Returns:
        搜索结果的字符串表示
    """
    try:
        # 这里应该实现真实的网络搜索逻辑
        # 目前返回占位符响应
        logger.info(f"执行网络搜索: {query}")

        # 模拟搜索结果
        results = [
            {"title": "搜索结果1", "url": "http://example.com/1", "snippet": "这是搜索结果1的摘要"},
            {"title": "搜索结果2", "url": "http://example.com/2", "snippet": "这是搜索结果2的摘要"}
        ]

        # 格式化搜索结果为字符串
        result_text = f"搜索关键词: {query}\n\n搜索结果:\n"
        for i, result in enumerate(results, 1):
            result_text += f"{i}. {result['title']}\n"
            result_text += f"   链接: {result['url']}\n"
            result_text += f"   摘要: {result['snippet']}\n\n"

        return result_text.strip()
    except Exception as e:
        logger.error(f"网络搜索 '{query}' 失败: {e}")
        return f"搜索失败: {str(e)}"

# 注册自定义工具
def get_custom_tools() -> list:
    """获取所有自定义工具"""
    return [
        calculator,
        web_search
    ]