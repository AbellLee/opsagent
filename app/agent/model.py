from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models import BaseLanguageModel
from langchain_community.llms import Tongyi
from app.core.config import settings
from app.core.logger import logger
import os

class QwenModel:
    """通义千问模型集成"""
    
    def __init__(self):
        self.model: Optional[BaseLanguageModel] = None
        # 不在初始化时加载模型，避免配置未加载的问题
    
    def _ensure_model(self):
        """确保模型已初始化"""
        if self.model is None:
            self._initialize_model()
    
    def _initialize_model(self):
        """初始化通义模型"""
        try:
            # 记录配置信息用于调试
            logger.info(f"检查通义API密钥配置: {getattr(settings, 'tongyi_api_key', 'NOT_SET')}")
            logger.info(f"检查通义模型名称配置: {getattr(settings, 'tongyi_model_name', 'NOT_SET')}")
            
            # 检查配置是否已加载
            if not hasattr(settings, 'tongyi_api_key') or not settings.tongyi_api_key:
                logger.warning("未配置通义API密钥，将无法使用模型功能")
                return
            
            # 同时设置环境变量以确保dashscope能正确读取
            os.environ['DASHSCOPE_API_KEY'] = settings.tongyi_api_key
            
            self.model = Tongyi(
                dashscope_api_key=settings.tongyi_api_key,
                model_name=getattr(settings, 'tongyi_model_name', 'qwen-plus')
            )
            logger.info(f"通义模型初始化成功: {getattr(settings, 'tongyi_model_name', 'qwen-plus')}")
        except Exception as e:
            logger.error(f"通义模型初始化失败: {e}")
    
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """生成模型响应"""
        self._ensure_model()
        
        if not self.model:
            error_msg = "模型未初始化，请检查是否已配置通义API密钥"
            logger.warning(error_msg)
            return error_msg
        
        # 检查消息是否为空
        if not messages:
            error_msg = "没有输入消息"
            logger.warning(error_msg)
            return error_msg
        
        logger.info(f"准备发送给模型的消息: {messages}")
        
        try:
            # 转换消息格式
            langchain_messages = []
            for msg in messages:
                # 确保消息内容不为空
                content = msg.get("content", "")
                if not content:
                    continue
                    
                role = msg.get("role", "user")
                if role == "system":
                    langchain_messages.append(SystemMessage(content=content))
                elif role == "user" or role == "human":
                    langchain_messages.append(HumanMessage(content=content))
                elif role == "assistant" or role == "ai":
                    langchain_messages.append(AIMessage(content=content))
            
            # 检查是否有有效消息
            if not langchain_messages:
                error_msg = "没有有效的输入消息"
                logger.warning(error_msg)
                return error_msg
            
            # 调用模型生成响应
            logger.info("正在调用模型...")
            response = self.model.invoke(langchain_messages)
            logger.info(f"模型返回响应: {response}")
            return response
        except Exception as e:
            error_msg = f"模型调用失败: {str(e)}"
            logger.error(error_msg)
            # 如果是API密钥问题，提供更明确的提示
            if "api key" in str(e).lower():
                return "模型调用失败：未配置通义API密钥。请配置DASHSCOPE_API_KEY环境变量或在配置文件中设置tongyi_api_key。"
            return error_msg

# 全局模型实例
qwen_model = QwenModel()