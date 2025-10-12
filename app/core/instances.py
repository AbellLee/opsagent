"""全局实例管理模块，用于避免循环导入问题"""
from typing import Optional, Any

# 全局变量存储初始化的实例
llm_instance: Optional[Any] = None
embedding_instance: Optional[Any] = None
graph_instance: Optional[Any] = None

def set_llm_instance(llm, embedding):
    """设置预初始化的LLM实例"""
    global llm_instance, embedding_instance
    llm_instance = llm
    embedding_instance = embedding

def get_llm_instance():
    """获取预初始化的LLM实例"""
    global llm_instance, embedding_instance
    return llm_instance, embedding_instance

def set_graph_instance(graph):
    """设置预初始化的Graph实例"""
    global graph_instance
    graph_instance = graph

def get_graph_instance():
    """获取预初始化的Graph实例"""
    global graph_instance
    return graph_instance