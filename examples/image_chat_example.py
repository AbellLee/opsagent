"""
图片聊天示例

演示如何使用 API 发送包含图片的消息
"""
import requests
import base64
import json
from pathlib import Path


def image_to_base64(image_path: str) -> str:
    """将图片文件转换为 base64 编码"""
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # 获取文件扩展名
    ext = Path(image_path).suffix.lower()
    mime_type = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }.get(ext, 'image/jpeg')
    
    # 编码为 base64
    base64_data = base64.b64encode(image_data).decode('utf-8')
    
    # 返回 data URL 格式
    return f"data:{mime_type};base64,{base64_data}"


def send_image_message(
    session_id: str,
    message: str,
    image_paths: list = None,
    image_urls: list = None,
    response_mode: str = "blocking",
    base_url: str = "http://localhost:8000"
):
    """
    发送包含图片的消息
    
    Args:
        session_id: 会话 ID
        message: 文本消息
        image_paths: 本地图片路径列表
        image_urls: 图片 URL 列表
        response_mode: 响应模式 (blocking 或 streaming)
        base_url: API 基础 URL
    
    Returns:
        API 响应
    """
    # 构建文件列表
    files = []
    
    # 添加本地图片
    if image_paths:
        for path in image_paths:
            base64_data = image_to_base64(path)
            files.append({
                "type": "image",
                "data": base64_data
            })
    
    # 添加 URL 图片
    if image_urls:
        for url in image_urls:
            files.append({
                "type": "image",
                "url": url
            })
    
    # 构建请求数据
    request_data = {
        "message": message,
        "response_mode": response_mode
    }
    
    if files:
        request_data["files"] = files
    
    # 发送请求
    url = f"{base_url}/api/sessions/{session_id}/chat"
    response = requests.post(url, json=request_data)
    
    return response.json()


# 示例 1: 发送单张图片
def example_single_image():
    """示例: 发送单张图片"""
    print("=== 示例 1: 发送单张图片 ===")
    
    session_id = "your-session-id"
    
    response = send_image_message(
        session_id=session_id,
        message="这张图片里有什么?",
        image_paths=["path/to/your/image.jpg"]
    )
    
    print(f"响应: {response}")


# 示例 2: 发送多张图片
def example_multiple_images():
    """示例: 发送多张图片"""
    print("\n=== 示例 2: 发送多张图片 ===")
    
    session_id = "your-session-id"
    
    response = send_image_message(
        session_id=session_id,
        message="比较这两张图片的区别",
        image_paths=[
            "path/to/image1.jpg",
            "path/to/image2.jpg"
        ]
    )
    
    print(f"响应: {response}")


# 示例 3: 使用图片 URL
def example_image_url():
    """示例: 使用图片 URL"""
    print("\n=== 示例 3: 使用图片 URL ===")
    
    session_id = "your-session-id"
    
    response = send_image_message(
        session_id=session_id,
        message="分析这张图片",
        image_urls=["https://example.com/image.jpg"]
    )
    
    print(f"响应: {response}")


# 示例 4: 只发送图片,不发送文本
def example_image_only():
    """示例: 只发送图片"""
    print("\n=== 示例 4: 只发送图片 ===")
    
    session_id = "your-session-id"
    
    response = send_image_message(
        session_id=session_id,
        message="",  # 空文本
        image_paths=["path/to/image.jpg"]
    )
    
    print(f"响应: {response}")


# 示例 5: 流式模式
def example_streaming():
    """示例: 流式模式发送图片"""
    print("\n=== 示例 5: 流式模式 ===")
    
    session_id = "your-session-id"
    base_url = "http://localhost:8000"
    
    # 准备数据
    image_base64 = image_to_base64("path/to/image.jpg")
    
    request_data = {
        "message": "描述这张图片",
        "response_mode": "streaming",
        "files": [
            {
                "type": "image",
                "data": image_base64
            }
        ]
    }
    
    # 发送请求并处理流式响应
    url = f"{base_url}/api/sessions/{session_id}/chat"
    response = requests.post(url, json=request_data, stream=True)
    
    print("流式响应:")
    for line in response.iter_lines():
        if line:
            # 解析 SSE 数据
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                data_str = line_str[6:]  # 去掉 'data: ' 前缀
                try:
                    data = json.loads(data_str)
                    if 'chunk' in data:
                        print(data['chunk'], end='', flush=True)
                except json.JSONDecodeError:
                    pass
    
    print("\n流式响应结束")


# 示例 6: 混合本地图片和 URL 图片
def example_mixed_sources():
    """示例: 混合使用本地图片和 URL 图片"""
    print("\n=== 示例 6: 混合图片来源 ===")
    
    session_id = "your-session-id"
    
    response = send_image_message(
        session_id=session_id,
        message="比较这些图片",
        image_paths=["path/to/local/image.jpg"],
        image_urls=["https://example.com/remote/image.jpg"]
    )
    
    print(f"响应: {response}")


# 示例 7: 使用 curl 命令
def example_curl_command():
    """示例: 等效的 curl 命令"""
    print("\n=== 示例 7: curl 命令 ===")
    
    curl_command = """
curl -X POST http://localhost:8000/api/sessions/{session_id}/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "这是什么图片?",
    "response_mode": "blocking",
    "files": [
      {
        "type": "image",
        "url": "https://example.com/image.jpg"
      }
    ]
  }'
"""
    
    print(curl_command)


if __name__ == "__main__":
    print("图片聊天 API 使用示例")
    print("=" * 50)
    
    # 注意: 运行前请替换 session_id 和图片路径
    
    # 取消注释以运行示例
    # example_single_image()
    # example_multiple_images()
    # example_image_url()
    # example_image_only()
    # example_streaming()
    # example_mixed_sources()
    example_curl_command()
    
    print("\n" + "=" * 50)
    print("提示:")
    print("1. 请确保使用支持多模态的 LLM 模型")
    print("2. 图片大小建议不超过 5MB")
    print("3. 支持的格式: JPG, PNG, GIF, WebP")
    print("4. 可以同时发送多张图片")
    print("5. 可以只发送图片而不发送文本")

