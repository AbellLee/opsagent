"""
Agent API路由模块
负责处理与Agent相关的HTTP请求
"""
from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from app.core.logger import logger

# 导入服务层模块
from app.services.agent.models import AgentExecuteRequest, AgentChatRequest
from app.services.agent.handlers import execute_agent_task, handle_blocking_chat, handle_streaming_chat
from app.services.agent.utils import build_agent_inputs, create_agent_config, format_error_message

# 创建路由器
router = APIRouter(prefix="/api/sessions", tags=["agent"])


@router.post("/{session_id}/execute")
async def execute_agent(
    session_id: UUID,
    request: AgentExecuteRequest,
):
    """执行Agent任务"""
    try:
        result = await execute_agent_task(
            session_id=session_id,
            message=request.message,
            tools=request.tools,
            config=request.config
        )
        return result

    except Exception as e:
        logger.error(f"与Agent聊天失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"与Agent聊天失败: {str(e)}"
        )


@router.post("/{session_id}/chat")
async def chat_with_agent(
    session_id: UUID,
    request: AgentChatRequest,
):
    """与Agent聊天（支持连续对话和流式响应）"""
    try:
        # 检查消息是否为空
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="消息内容不能为空"
            )

        # 构造输入和配置
        inputs = build_agent_inputs(request.message, session_id)
        config = create_agent_config(session_id)

        # 根据响应模式选择处理方式
        if request.response_mode == "streaming":
            return await handle_streaming_chat(session_id, inputs, config)
        else:
            return await handle_blocking_chat(session_id, inputs, config)


    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"与Agent聊天失败: {str(e)}")
        error_detail = format_error_message(e)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"与Agent聊天失败: {error_detail}"
        )

