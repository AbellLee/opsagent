"""
测试多模态消息格式的兼容性

验证前端和后端使用的消息格式是否一致
"""


def test_langchain_message_format():
    """测试 LangChain 标准的多模态消息格式"""
    
    # LangChain 标准格式 - 使用 "text" 字段
    langchain_format = [
        {
            "type": "text",
            "text": "这个是什么?"  # 注意: 使用 "text" 字段
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "data:image/gif;base64,R0lGODlh..."
            }
        }
    ]
    
    # 验证格式
    assert langchain_format[0]["type"] == "text"
    assert "text" in langchain_format[0]
    assert langchain_format[0]["text"] == "这个是什么?"
    
    assert langchain_format[1]["type"] == "image_url"
    assert "image_url" in langchain_format[1]
    assert "url" in langchain_format[1]["image_url"]
    
    print("✓ LangChain 标准格式验证通过")


def test_frontend_message_format():
    """测试前端发送的消息格式"""
    
    # 模拟前端构建的消息内容
    message_content = "这个是什么?"
    images = [
        {
            "type": "image",
            "url": "data:image/gif;base64,R0lGODlh...",
            "data": "data:image/gif;base64,R0lGODlh..."
        }
    ]
    
    # 前端构建逻辑
    user_message_content = []
    if message_content:
        user_message_content.append({
            "type": "text",
            "text": message_content  # 使用 "text" 字段
        })
    
    for img in images:
        user_message_content.append({
            "type": "image_url",
            "image_url": {
                "url": img["url"]
            }
        })
    
    # 验证格式
    assert len(user_message_content) == 2
    assert user_message_content[0]["type"] == "text"
    assert user_message_content[0]["text"] == "这个是什么?"
    assert user_message_content[1]["type"] == "image_url"
    
    print("✓ 前端消息格式验证通过")


def test_backend_message_format():
    """测试后端构建的消息格式"""
    from app.services.agent.utils import build_agent_inputs
    from uuid import uuid4
    
    session_id = uuid4()
    message = "这个是什么?"
    files = [
        {
            "type": "image",
            "url": "data:image/gif;base64,R0lGODlh..."
        }
    ]
    
    # 后端构建消息
    inputs = build_agent_inputs(message, session_id, files=files)
    
    # 验证格式
    content = inputs["messages"][0].content
    assert isinstance(content, list)
    assert len(content) == 2
    
    # 验证文本部分使用 "text" 字段
    assert content[0]["type"] == "text"
    assert "text" in content[0]
    assert content[0]["text"] == "这个是什么?"
    
    # 验证图片部分
    assert content[1]["type"] == "image_url"
    assert "image_url" in content[1]
    assert "url" in content[1]["image_url"]
    
    print("✓ 后端消息格式验证通过")


def test_frontend_display_compatibility():
    """测试前端显示组件的兼容性"""
    
    # 模拟 ChatMessage.vue 的渲染逻辑
    def get_text_content(item):
        """模拟前端获取文本内容的逻辑"""
        return item.get("content") or item.get("text") or ""
    
    # 测试使用 "text" 字段的格式 (LangChain 标准)
    item_with_text = {
        "type": "text",
        "text": "这个是什么?"
    }
    assert get_text_content(item_with_text) == "这个是什么?"
    
    # 测试使用 "content" 字段的格式 (旧格式)
    item_with_content = {
        "type": "text",
        "content": "这是旧格式"
    }
    assert get_text_content(item_with_content) == "这是旧格式"
    
    # 测试同时有两个字段的情况 (优先使用 content)
    item_with_both = {
        "type": "text",
        "content": "content 字段",
        "text": "text 字段"
    }
    assert get_text_content(item_with_both) == "content 字段"
    
    print("✓ 前端显示兼容性验证通过")


def test_complete_flow():
    """测试完整的消息流程"""
    from app.services.agent.utils import build_agent_inputs
    from uuid import uuid4
    
    # 1. 前端构建用户消息
    message_content = "这个是什么?"
    images = [{"type": "image", "data": "data:image/gif;base64,R0lGODlh..."}]
    
    user_message_content = []
    if message_content:
        user_message_content.append({
            "type": "text",
            "text": message_content
        })
    
    for img in images:
        user_message_content.append({
            "type": "image_url",
            "image_url": {"url": img["data"]}
        })
    
    # 2. 后端接收并构建 LangChain 消息
    session_id = uuid4()
    files = [{"type": "image", "data": "data:image/gif;base64,R0lGODlh..."}]
    inputs = build_agent_inputs(message_content, session_id, files=files)
    
    # 3. 验证后端构建的消息格式与前端一致
    backend_content = inputs["messages"][0].content
    
    assert len(backend_content) == len(user_message_content)
    assert backend_content[0]["type"] == user_message_content[0]["type"]
    assert backend_content[0]["text"] == user_message_content[0]["text"]
    assert backend_content[1]["type"] == user_message_content[1]["type"]
    
    # 4. 模拟前端显示
    def get_text_content(item):
        return item.get("content") or item.get("text") or ""
    
    displayed_text = get_text_content(backend_content[0])
    assert displayed_text == "这个是什么?"
    
    print("✓ 完整流程验证通过")
    print(f"  - 前端发送: {user_message_content[0]}")
    print(f"  - 后端构建: {backend_content[0]}")
    print(f"  - 前端显示: {displayed_text}")


if __name__ == "__main__":
    print("=" * 60)
    print("测试多模态消息格式兼容性")
    print("=" * 60)
    
    test_langchain_message_format()
    test_frontend_message_format()
    test_backend_message_format()
    test_frontend_display_compatibility()
    test_complete_flow()
    
    print("=" * 60)
    print("所有测试通过! ✓")
    print("=" * 60)
    print("\n总结:")
    print("1. 前端和后端都使用 'text' 字段(LangChain 标准)")
    print("2. 前端显示组件兼容 'content' 和 'text' 两种格式")
    print("3. 完整的消息流程格式一致")

