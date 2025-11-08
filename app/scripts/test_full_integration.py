#!/usr/bin/env python3
"""
完整集成测试脚本
测试 LLM 多模型支持的所有功能
"""

import requests
import json
import time
from uuid import uuid4

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"
DIFY_BASE = f"{BASE_URL}/v1"

# 测试用户
TEST_USER_ID = str(uuid4())
TEST_USERNAME = "test_user"

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_llm_config_api():
    """测试 LLM 配置 API"""
    print_section("测试 LLM 配置 API")
    
    # 1. 获取提供商列表
    print("1. 获取支持的提供商...")
    response = requests.get(f"{API_BASE}/llm-configs/providers")
    if response.status_code == 200:
        providers = response.json()
        print(f"✓ 支持的提供商: {', '.join(providers)}")
    else:
        print(f"✗ 获取提供商失败: {response.status_code}")
        return False
    
    # 2. 创建测试配置
    print("\n2. 创建测试配置...")
    test_config = {
        "name": "测试配置 - OpenAI",
        "provider": "openai",
        "model_name": "gpt-4o-mini",
        "api_key": "sk-test-key",
        "base_url": "https://api.openai.com/v1",
        "is_embedding": False,
        "is_active": True,
        "is_default": True,
        "description": "测试用配置"
    }
    
    response = requests.post(f"{API_BASE}/llm-configs/", json=test_config)
    if response.status_code == 200:
        config = response.json()
        config_id = config["id"]
        print(f"✓ 配置创建成功: {config['name']} (ID: {config_id})")
    else:
        print(f"✗ 配置创建失败: {response.status_code} - {response.text}")
        return False
    
    # 3. 获取配置列表
    print("\n3. 获取配置列表...")
    response = requests.get(f"{API_BASE}/llm-configs/")
    if response.status_code == 200:
        configs = response.json()
        print(f"✓ 当前有 {len(configs)} 个配置")
        for cfg in configs:
            status_icon = "✓" if cfg["is_active"] else "✗"
            default_icon = "[默认]" if cfg["is_default"] else ""
            print(f"  {status_icon} {cfg['name']} ({cfg['provider']}) {default_icon}")
    else:
        print(f"✗ 获取配置列表失败: {response.status_code}")
        return False
    
    # 4. 获取默认配置
    print("\n4. 获取默认配置...")
    response = requests.get(f"{API_BASE}/llm-configs/default?is_embedding=false")
    if response.status_code == 200:
        default_config = response.json()
        print(f"✓ 默认配置: {default_config['name']}")
    else:
        print(f"✗ 获取默认配置失败: {response.status_code}")
    
    # 5. 更新配置
    print("\n5. 更新配置...")
    update_data = {
        "description": "更新后的测试配置"
    }
    response = requests.put(f"{API_BASE}/llm-configs/{config_id}", json=update_data)
    if response.status_code == 200:
        updated_config = response.json()
        print(f"✓ 配置更新成功: {updated_config['description']}")
    else:
        print(f"✗ 配置更新失败: {response.status_code}")
    
    # 6. 切换激活状态
    print("\n6. 切换激活状态...")
    response = requests.post(f"{API_BASE}/llm-configs/{config_id}/toggle-status")
    if response.status_code == 200:
        toggled_config = response.json()
        print(f"✓ 激活状态切换成功: {toggled_config['is_active']}")
    else:
        print(f"✗ 切换激活状态失败: {response.status_code}")
    
    # 恢复激活状态
    requests.post(f"{API_BASE}/llm-configs/{config_id}/toggle-status")
    
    return config_id

def test_session_with_model(config_id):
    """测试带模型的会话创建"""
    print_section("测试会话创建（指定模型）")
    
    # 1. 创建带模型的会话
    print("1. 创建带模型的会话...")
    session_data = {
        "user_id": TEST_USER_ID,
        "llm_config_id": config_id
    }
    
    response = requests.post(f"{API_BASE}/sessions", json=session_data)
    if response.status_code == 201:
        session = response.json()
        session_id = session["session_id"]
        print(f"✓ 会话创建成功: {session_id}")
        print(f"  LLM 配置 ID: {session.get('llm_config_id')}")
    else:
        print(f"✗ 会话创建失败: {response.status_code} - {response.text}")
        return None
    
    # 2. 获取会话详情
    print("\n2. 获取会话详情...")
    response = requests.get(f"{API_BASE}/sessions/{session_id}")
    if response.status_code == 200:
        session_detail = response.json()
        print(f"✓ 会话详情获取成功")
        print(f"  会话名称: {session_detail['session_name']}")
        print(f"  LLM 配置 ID: {session_detail.get('llm_config_id')}")
    else:
        print(f"✗ 获取会话详情失败: {response.status_code}")
    
    return session_id

def test_session_without_model():
    """测试不指定模型的会话创建（使用默认）"""
    print_section("测试会话创建（使用默认模型）")
    
    print("创建不指定模型的会话...")
    session_data = {
        "user_id": TEST_USER_ID
    }
    
    response = requests.post(f"{API_BASE}/sessions", json=session_data)
    if response.status_code == 201:
        session = response.json()
        session_id = session["session_id"]
        print(f"✓ 会话创建成功: {session_id}")
        print(f"  LLM 配置 ID: {session.get('llm_config_id', '未指定（使用默认）')}")
        return session_id
    else:
        print(f"✗ 会话创建失败: {response.status_code} - {response.text}")
        return None

def test_dify_api_with_model(config_id):
    """测试 Dify API（指定模型）"""
    print_section("测试 Dify API（指定模型）")
    
    print("发送聊天请求（阻塞模式）...")
    chat_request = {
        "query": "你好，请简单介绍一下你自己",
        "user": TEST_USERNAME,
        "response_mode": "blocking",
        "model_config_id": config_id
    }
    
    try:
        response = requests.post(f"{DIFY_BASE}/chat-messages", json=chat_request, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 聊天请求成功")
            print(f"  会话 ID: {result.get('conversation_id')}")
            print(f"  消息 ID: {result.get('message_id')}")
            print(f"  回复: {result.get('answer', '')[:100]}...")
        else:
            print(f"✗ 聊天请求失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ 聊天请求异常: {e}")

def test_dify_api_without_model():
    """测试 Dify API（使用默认模型）"""
    print_section("测试 Dify API（使用默认模型）")
    
    print("发送聊天请求（阻塞模式）...")
    chat_request = {
        "query": "你好",
        "user": TEST_USERNAME,
        "response_mode": "blocking"
    }
    
    try:
        response = requests.post(f"{DIFY_BASE}/chat-messages", json=chat_request, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 聊天请求成功")
            print(f"  会话 ID: {result.get('conversation_id')}")
            print(f"  消息 ID: {result.get('message_id')}")
            print(f"  回复: {result.get('answer', '')[:100]}...")
        else:
            print(f"✗ 聊天请求失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ 聊天请求异常: {e}")

def cleanup(config_id):
    """清理测试数据"""
    print_section("清理测试数据")
    
    if config_id:
        print(f"删除测试配置: {config_id}...")
        response = requests.delete(f"{API_BASE}/llm-configs/{config_id}")
        if response.status_code == 200:
            print("✓ 测试配置已删除")
        else:
            print(f"✗ 删除测试配置失败: {response.status_code}")

def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("  OpsAgent LLM 多模型支持 - 完整集成测试")
    print("="*60)
    
    print(f"\n测试服务器: {BASE_URL}")
    print(f"测试用户 ID: {TEST_USER_ID}")
    
    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code != 200:
            print("\n✗ 服务器未运行或无法访问")
            print("  请先启动后端服务: cd app && python main.py")
            return
    except Exception as e:
        print(f"\n✗ 无法连接到服务器: {e}")
        print("  请先启动后端服务: cd app && python main.py")
        return
    
    config_id = None
    
    try:
        # 1. 测试 LLM 配置 API
        config_id = test_llm_config_api()
        if not config_id:
            print("\n✗ LLM 配置 API 测试失败，终止测试")
            return
        
        time.sleep(1)
        
        # 2. 测试带模型的会话创建
        session_id = test_session_with_model(config_id)
        
        time.sleep(1)
        
        # 3. 测试不指定模型的会话创建
        test_session_without_model()
        
        time.sleep(1)
        
        # 4. 测试 Dify API（指定模型）
        # 注意：这需要有效的 API Key，可能会失败
        # test_dify_api_with_model(config_id)
        
        # time.sleep(1)
        
        # 5. 测试 Dify API（默认模型）
        # test_dify_api_without_model()
        
        print_section("测试总结")
        print("✓ 所有基础功能测试完成！")
        print("\n注意：")
        print("  - Dify API 测试已跳过（需要有效的 API Key）")
        print("  - 如需测试 Dify API，请取消注释相关代码并配置有效的 API Key")
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n✗ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试数据
        if config_id:
            cleanup(config_id)

if __name__ == "__main__":
    main()

