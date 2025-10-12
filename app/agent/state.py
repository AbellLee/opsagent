from typing import Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState

# 使用简单的MessagesState，避免复杂类型定义导致的问题
AgentState = MessagesState