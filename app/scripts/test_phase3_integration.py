#!/usr/bin/env python3
"""测试第三阶段：API 集成和 Dify 兼容"""
import sys
import os
import requests
import json
from uuid import uuid4

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from app.core.logger import logger

# API 基础 URL
BASE_URL = "http://localhost:8000"


def test_llm_configs_api():
    """测试 LLM 配置 API"""
    logger.info("\n" + "="*50)
    logger.info("测试 LLM 配置 API")
    logger.info("="*50)
    
    # 1. 获取所有配置
    logger.info("\n1. 获取所有 LLM 配置...")
    response = requests.get(f"{BASE_URL}/api/llm-configs/")
    if response.status_code == 200:
        configs = response.json()
        logger.info(f"✓ 成功获取 {len(configs)} 个配置")
        for config in configs:
            logger.info(f"  - {config['name']} ({config['provider']}) - {'激活' if config['is_active'] else '未激活'}")
    else:
        logger.error(f"✗ 获取配置失败: {response.status_code} - {response.text}")
        return None
    
    # 2. 获取默认聊天模型配置
    logger.info("\n2. 获取默认聊天模型配置...")
    response = requests.get(f"{BASE_URL}/api/llm-configs/default?is_embedding=false")
    if response.status_code == 200:
        default_config = response.json()
        logger.info(f"✓ 默认聊天模型: {default_config['name']} (ID: {default_config['id']})")
        return default_config['id']
    else:
        logger.error(f"✗ 获取默认配置失败: {response.status_code} - {response.text}")
        return None


def test_session_with_llm_config(llm_config_id):
    """测试创建带 LLM 配置的会话"""
    logger.info("\n" + "="*50)
    logger.info("测试创建带 LLM 配置的会话")
    logger.info("="*50)
    
    # 创建测试用户
    user_id = str(uuid4())
    logger.info(f"\n使用测试用户 ID: {user_id}")
    
    # 创建会话（指定 LLM 配置）
    logger.info(f"\n创建会话（使用 LLM 配置: {llm_config_id}）...")
    session_data = {
        "user_id": user_id,
        "llm_config_id": llm_config_id
    }
    response = requests.post(f"{BASE_URL}/api/sessions", json=session_data)
    if response.status_code == 201:
        session = response.json()
        logger.info(f"✓ 会话创建成功: {session['session_id']}")
        logger.info(f"  - LLM 配置 ID: {session.get('llm_config_id')}")
        return session['session_id']
    else:
        logger.error(f"✗ 创建会话失败: {response.status_code} - {response.text}")
        return None


def test_dify_api_with_model_config(llm_config_id):
    """测试 Dify API 的模型配置支持"""
    logger.info("\n" + "="*50)
    logger.info("测试 Dify API 的模型配置支持")
    logger.info("="*50)
    
    # 测试阻塞模式
    logger.info("\n1. 测试阻塞模式（指定模型配置）...")
    request_data = {
        "query": "你好，请介绍一下你自己",
        "user": "test_user",
        "response_mode": "blocking",
        "model_config_id": llm_config_id
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat-messages",
            json=request_data,
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✓ 阻塞模式测试成功")
            logger.info(f"  - 会话 ID: {result.get('conversation_id')}")
            logger.info(f"  - 回复: {result.get('answer', '')[:100]}...")
            return result.get('conversation_id')
        else:
            logger.error(f"✗ 阻塞模式测试失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"✗ 阻塞模式测试异常: {e}")
        return None


def test_dify_streaming_with_model_config(llm_config_id):
    """测试 Dify API 流式模式的模型配置支持"""
    logger.info("\n2. 测试流式模式（指定模型配置）...")
    request_data = {
        "query": "请用一句话介绍 Python",
        "user": "test_user",
        "response_mode": "streaming",
        "model_config_id": llm_config_id
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat-messages",
            json=request_data,
            stream=True,
            timeout=30
        )
        if response.status_code == 200:
            logger.info(f"✓ 流式模式测试成功")
            logger.info("  - 接收到的事件:")
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 去掉 "data: " 前缀
                        try:
                            event = json.loads(data_str)
                            event_type = event.get('event')
                            if event_type == 'message':
                                logger.info(f"    * 消息开始")
                            elif event_type == 'agent_message':
                                content = event.get('answer', '')
                                if content:
                                    logger.info(f"    * 内容: {content[:50]}...")
                            elif event_type == 'message_end':
                                logger.info(f"    * 消息结束")
                        except json.JSONDecodeError:
                            pass
            return True
        else:
            logger.error(f"✗ 流式模式测试失败: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ 流式模式测试异常: {e}")
        return False


def test_session_without_llm_config():
    """测试创建不指定 LLM 配置的会话（使用默认配置）"""
    logger.info("\n" + "="*50)
    logger.info("测试创建不指定 LLM 配置的会话（使用默认配置）")
    logger.info("="*50)
    
    user_id = str(uuid4())
    logger.info(f"\n使用测试用户 ID: {user_id}")
    
    session_data = {
        "user_id": user_id
    }
    response = requests.post(f"{BASE_URL}/api/sessions", json=session_data)
    if response.status_code == 201:
        session = response.json()
        logger.info(f"✓ 会话创建成功: {session['session_id']}")
        logger.info(f"  - LLM 配置 ID: {session.get('llm_config_id', 'None (使用默认)')}")
        return True
    else:
        logger.error(f"✗ 创建会话失败: {response.status_code} - {response.text}")
        return False


if __name__ == "__main__":
    logger.info("开始测试第三阶段：API 集成和 Dify 兼容...")
    
    # 确保服务器正在运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            logger.error("✗ 服务器未运行或健康检查失败")
            logger.error("请先启动服务器: cd app && python main.py")
            sys.exit(1)
        logger.info("✓ 服务器运行正常")
    except Exception as e:
        logger.error(f"✗ 无法连接到服务器: {e}")
        logger.error("请先启动服务器: cd app && python main.py")
        sys.exit(1)
    
    # 测试 LLM 配置 API
    llm_config_id = test_llm_configs_api()
    if not llm_config_id:
        logger.error("✗ 无法获取 LLM 配置，测试终止")
        sys.exit(1)
    
    # 测试会话创建（带 LLM 配置）
    session_id = test_session_with_llm_config(llm_config_id)
    
    # 测试会话创建（不指定 LLM 配置）
    test_session_without_llm_config()
    
    # 测试 Dify API（阻塞模式）
    conversation_id = test_dify_api_with_model_config(llm_config_id)
    
    # 测试 Dify API（流式模式）
    if conversation_id:
        test_dify_streaming_with_model_config(llm_config_id)
    
    logger.info("\n" + "="*50)
    logger.info("✓ 第三阶段测试完成！")
    logger.info("="*50)

