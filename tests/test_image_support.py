"""
测试图片支持功能
"""
import pytest
from app.services.agent.utils import build_agent_inputs
from uuid import uuid4


def test_build_agent_inputs_text_only():
    """测试纯文本消息"""
    session_id = uuid4()
    message = "你好"
    
    inputs = build_agent_inputs(message, session_id)
    
    assert "messages" in inputs
    assert len(inputs["messages"]) == 1
    assert inputs["messages"][0].content == "你好"


def test_build_agent_inputs_with_single_image():
    """测试单张图片消息"""
    session_id = uuid4()
    message = "这是什么?"
    files = [
        {
            "type": "image",
            "url": "https://example.com/image.jpg"
        }
    ]
    
    inputs = build_agent_inputs(message, session_id, files=files)
    
    assert "messages" in inputs
    assert len(inputs["messages"]) == 1
    
    content = inputs["messages"][0].content
    assert isinstance(content, list)
    assert len(content) == 2  # 文本 + 图片
    
    # 检查文本内容
    assert content[0]["type"] == "text"
    assert content[0]["text"] == "这是什么?"
    
    # 检查图片内容
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"] == "https://example.com/image.jpg"


def test_build_agent_inputs_with_multiple_images():
    """测试多张图片消息"""
    session_id = uuid4()
    message = "比较这两张图片"
    files = [
        {
            "type": "image",
            "url": "https://example.com/image1.jpg"
        },
        {
            "type": "image",
            "data": "data:image/jpeg;base64,/9j/4AAQ..."
        }
    ]
    
    inputs = build_agent_inputs(message, session_id, files=files)
    
    content = inputs["messages"][0].content
    assert isinstance(content, list)
    assert len(content) == 3  # 文本 + 2张图片
    
    # 检查文本
    assert content[0]["type"] == "text"
    
    # 检查第一张图片
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"] == "https://example.com/image1.jpg"
    
    # 检查第二张图片
    assert content[2]["type"] == "image_url"
    assert content[2]["image_url"]["url"] == "data:image/jpeg;base64,/9j/4AAQ..."


def test_build_agent_inputs_image_only():
    """测试只有图片没有文本的消息"""
    session_id = uuid4()
    message = ""
    files = [
        {
            "type": "image",
            "url": "https://example.com/image.jpg"
        }
    ]
    
    inputs = build_agent_inputs(message, session_id, files=files)
    
    content = inputs["messages"][0].content
    assert isinstance(content, list)
    assert len(content) == 1  # 只有图片
    
    # 检查图片内容
    assert content[0]["type"] == "image_url"
    assert content[0]["image_url"]["url"] == "https://example.com/image.jpg"


def test_build_agent_inputs_with_base64_image():
    """测试 base64 编码的图片"""
    session_id = uuid4()
    message = "分析这张图片"
    base64_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    files = [
        {
            "type": "image",
            "data": base64_data
        }
    ]
    
    inputs = build_agent_inputs(message, session_id, files=files)
    
    content = inputs["messages"][0].content
    assert isinstance(content, list)
    assert len(content) == 2
    
    # 检查图片使用了 base64 数据
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"] == base64_data


def test_build_agent_inputs_empty_files():
    """测试空文件列表"""
    session_id = uuid4()
    message = "你好"
    files = []
    
    inputs = build_agent_inputs(message, session_id, files=files)
    
    # 空文件列表应该和纯文本消息一样
    assert inputs["messages"][0].content == "你好"


def test_build_agent_inputs_none_files():
    """测试 None 文件列表"""
    session_id = uuid4()
    message = "你好"
    
    inputs = build_agent_inputs(message, session_id, files=None)
    
    # None 文件列表应该和纯文本消息一样
    assert inputs["messages"][0].content == "你好"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])

