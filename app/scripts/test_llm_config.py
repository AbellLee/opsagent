#!/usr/bin/env python3
"""测试 LLM 配置功能"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from app.db.session import get_db_sqlalchemy
from app.services.llm_service import LLMService
from app.models.pydantic_schemas.llm_config import LLMConfigCreate
from app.core.logger import logger


def test_create_default_configs():
    """创建默认的 LLM 配置"""
    db = next(get_db_sqlalchemy())
    llm_service = LLMService(db)
    
    try:
        # 1. 创建 OpenAI 聊天模型配置（默认）
        logger.info("创建 OpenAI 聊天模型配置...")
        openai_chat = LLMConfigCreate(
            name="OpenAI GPT-4o-mini",
            provider="openai",
            model_name="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY", "sk-dummy-key"),
            base_url="https://api.openai.com/v1",
            max_tokens=2048,
            temperature=0.7,
            description="OpenAI GPT-4o-mini 聊天模型",
            is_active=True,
            is_default=True,
            is_embedding=False
        )
        config1 = llm_service.create_config(openai_chat)
        logger.info(f"✓ 创建成功: {config1.name} (ID: {config1.id})")
        
        # 2. 创建 OpenAI 嵌入模型配置（默认）
        logger.info("创建 OpenAI 嵌入模型配置...")
        openai_embedding = LLMConfigCreate(
            name="OpenAI text-embedding-3-small",
            provider="openai",
            model_name="text-embedding-3-small",
            api_key=os.getenv("OPENAI_API_KEY", "sk-dummy-key"),
            base_url="https://api.openai.com/v1",
            description="OpenAI 文本嵌入模型",
            is_active=True,
            is_default=True,
            is_embedding=True
        )
        config2 = llm_service.create_config(openai_embedding)
        logger.info(f"✓ 创建成功: {config2.name} (ID: {config2.id})")
        
        # 3. 创建通义千问配置
        logger.info("创建通义千问配置...")
        tongyi_chat = LLMConfigCreate(
            name="通义千问 Turbo",
            provider="tongyi",
            model_name="qwen-turbo",
            api_key=os.getenv("DASHSCOPE_API_KEY", "sk-dummy-key"),
            max_tokens=2048,
            temperature=0.7,
            description="阿里云通义千问 Turbo 模型",
            is_active=True,
            is_default=False,
            is_embedding=False
        )
        config3 = llm_service.create_config(tongyi_chat)
        logger.info(f"✓ 创建成功: {config3.name} (ID: {config3.id})")
        
        # 4. 创建 DeepSeek 配置
        logger.info("创建 DeepSeek 配置...")
        deepseek_chat = LLMConfigCreate(
            name="DeepSeek Chat",
            provider="deepseek",
            model_name="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY", "sk-dummy-key"),
            base_url="https://api.deepseek.com/v1",
            max_tokens=4096,
            temperature=0.7,
            description="DeepSeek 聊天模型",
            is_active=True,
            is_default=False,
            is_embedding=False
        )
        config4 = llm_service.create_config(deepseek_chat)
        logger.info(f"✓ 创建成功: {config4.name} (ID: {config4.id})")
        
        # 5. 创建 Ollama 配置
        logger.info("创建 Ollama 配置...")
        ollama_chat = LLMConfigCreate(
            name="Ollama Llama3",
            provider="ollama",
            model_name="llama3",
            base_url="http://localhost:11434/v1",
            max_tokens=2048,
            temperature=0.7,
            description="本地 Ollama Llama3 模型",
            is_active=False,  # 默认不激活，因为需要本地部署
            is_default=False,
            is_embedding=False
        )
        config5 = llm_service.create_config(ollama_chat)
        logger.info(f"✓ 创建成功: {config5.name} (ID: {config5.id})")
        
        logger.info("\n" + "="*50)
        logger.info("所有默认配置创建成功！")
        logger.info("="*50)
        
        # 显示所有配置
        logger.info("\n当前所有配置:")
        all_configs = llm_service.search_configs()
        for config in all_configs:
            status = "✓ 激活" if config.is_active else "✗ 未激活"
            default = " [默认]" if config.is_default else ""
            model_type = "嵌入" if config.is_embedding else "聊天"
            logger.info(f"  - {config.name} ({model_type}) {status}{default}")
        
        # 显示默认配置
        logger.info("\n默认聊天模型:")
        default_chat = llm_service.get_default_config(is_embedding=False)
        if default_chat:
            logger.info(f"  {default_chat.name} - {default_chat.model_name}")
        
        logger.info("\n默认嵌入模型:")
        default_embedding = llm_service.get_default_config(is_embedding=True)
        if default_embedding:
            logger.info(f"  {default_embedding.name} - {default_embedding.model_name}")
        
    except Exception as e:
        logger.error(f"创建配置失败: {e}", exc_info=True)
        raise
    finally:
        db.close()


def test_get_model_instances():
    """测试获取模型实例"""
    db = next(get_db_sqlalchemy())
    llm_service = LLMService(db)
    
    try:
        logger.info("\n" + "="*50)
        logger.info("测试获取模型实例")
        logger.info("="*50)
        
        # 获取默认聊天模型
        logger.info("\n获取默认聊天模型...")
        chat_model = llm_service.get_chat_model()
        logger.info(f"✓ 成功获取聊天模型: {chat_model.model_name}")
        
        # 获取默认嵌入模型
        logger.info("\n获取默认嵌入模型...")
        try:
            embedding_model = llm_service.get_embedding_model()
            logger.info(f"✓ 成功获取嵌入模型")
        except Exception as e:
            logger.warning(f"获取嵌入模型失败: {e}")
        
        # 根据名称获取模型
        logger.info("\n根据名称获取模型...")
        tongyi_model = llm_service.get_chat_model(config_name="通义千问 Turbo")
        logger.info(f"✓ 成功获取通义千问模型: {tongyi_model.model_name}")
        
    except Exception as e:
        logger.error(f"获取模型实例失败: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始测试 LLM 配置功能...")
    
    # 测试创建默认配置
    test_create_default_configs()
    
    # 测试获取模型实例
    test_get_model_instances()
    
    logger.info("\n✓ 所有测试完成！")

