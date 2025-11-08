"""
Dify API 兼容性测试脚本
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_blocking_mode():
    """测试阻塞模式"""
    print("\n=== 测试阻塞模式 ===")
    
    url = f"{BASE_URL}/v1/chat-messages"
    
    data = {
        "inputs": {},
        "query": "你好，请简单介绍一下你自己",
        "response_mode": "blocking",
        "conversation_id": "",
        "user": "test-user-001"
    }
    
    print(f"发送请求: {json.dumps(data, ensure_ascii=False)}")
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ 请求成功")
        print(f"  - 消息ID: {result.get('message_id')}")
        print(f"  - 会话ID: {result.get('conversation_id')}")
        print(f"  - 回复: {result.get('answer')[:100]}...")
        return result.get('conversation_id')
    else:
        print(f"✗ 请求失败: {response.status_code}")
        print(f"  错误信息: {response.text}")
        return None


def test_streaming_mode(conversation_id=None):
    """测试流式模式"""
    print("\n=== 测试流式模式 ===")
    
    url = f"{BASE_URL}/v1/chat-messages"
    
    data = {
        "inputs": {},
        "query": "请用一句话总结你的功能",
        "response_mode": "streaming",
        "conversation_id": conversation_id or "",
        "user": "test-user-001"
    }
    
    print(f"发送请求: {json.dumps(data, ensure_ascii=False)}")
    
    response = requests.post(url, json=data, stream=True)
    
    if response.status_code == 200:
        print("✓ 开始接收流式响应:")
        
        full_answer = ""
        new_conversation_id = None
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        event_data = json.loads(line_str[6:])
                        event_type = event_data.get('event')
                        
                        if event_type == 'message':
                            print(f"  - 消息开始")
                            new_conversation_id = event_data.get('conversation_id')
                        
                        elif event_type == 'agent_message':
                            answer = event_data.get('answer', '')
                            full_answer += answer
                            print(f"  - 收到片段: {answer}", end='', flush=True)
                        
                        elif event_type == 'agent_thought':
                            thought = event_data.get('thought', '')
                            print(f"\n  - Agent思考: {thought}")
                        
                        elif event_type == 'message_end':
                            print(f"\n  - 消息结束")
                            print(f"  - 完整回复: {full_answer}")
                    
                    except json.JSONDecodeError as e:
                        print(f"\n  ✗ JSON解析错误: {e}")
        
        return new_conversation_id
    else:
        print(f"✗ 请求失败: {response.status_code}")
        print(f"  错误信息: {response.text}")
        return None


def test_get_conversation(conversation_id):
    """测试获取会话信息"""
    print("\n=== 测试获取会话信息 ===")
    
    url = f"{BASE_URL}/v1/conversations/{conversation_id}"
    
    print(f"获取会话: {conversation_id}")
    
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ 获取成功")
        print(f"  - 会话ID: {result.get('id')}")
        print(f"  - 会话名称: {result.get('name')}")
        print(f"  - 创建时间: {result.get('created_at')}")
    else:
        print(f"✗ 获取失败: {response.status_code}")
        print(f"  错误信息: {response.text}")


def test_delete_conversation(conversation_id):
    """测试删除会话"""
    print("\n=== 测试删除会话 ===")
    
    url = f"{BASE_URL}/v1/conversations/{conversation_id}"
    
    print(f"删除会话: {conversation_id}")
    
    response = requests.delete(url)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ 删除成功: {result}")
    else:
        print(f"✗ 删除失败: {response.status_code}")
        print(f"  错误信息: {response.text}")


def test_conversation_continuity():
    """测试会话连续性"""
    print("\n=== 测试会话连续性 ===")
    
    # 第一次对话
    print("\n第一次对话:")
    conversation_id = test_blocking_mode()
    
    if not conversation_id:
        print("✗ 无法创建会话，测试终止")
        return
    
    time.sleep(1)
    
    # 第二次对话（使用相同的会话ID）
    print(f"\n第二次对话（使用会话ID: {conversation_id}）:")
    test_streaming_mode(conversation_id)
    
    time.sleep(1)
    
    # 获取会话信息
    test_get_conversation(conversation_id)
    
    # 删除会话
    test_delete_conversation(conversation_id)


def main():
    """主测试函数"""
    print("=" * 60)
    print("Dify API 兼容性测试")
    print("=" * 60)
    
    try:
        # 测试阻塞模式
        conversation_id = test_blocking_mode()
        
        if conversation_id:
            time.sleep(1)
            
            # 测试流式模式
            test_streaming_mode()
            
            time.sleep(1)
            
            # 测试会话连续性
            test_conversation_continuity()
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

