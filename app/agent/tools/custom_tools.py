from typing import Dict, Any, List
from langchain_core.tools import tool
from app.core.logger import logger
from uuid import uuid4, UUID
import json
from datetime import datetime

# 数据库连接
from app.core.config import get_settings
import psycopg2
from psycopg2.extras import RealDictCursor

# 用户上下文管理
from app.core.user_context import get_user_id, get_session_id

settings = get_settings()


# 注册自定义工具
def get_custom_tools() -> list:
    """获取所有自定义工具"""
    return [
        add_tasks,
        update_tasks,
        get_tasks,
        delete_tasks
    ]


def _get_db_connection():
    """获取数据库连接"""
    return psycopg2.connect(settings.database_url)


def _check_user_exists(cursor, user_id: str) -> bool:
    """检查用户是否存在"""
    cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
    return cursor.fetchone() is not None


def _check_session_exists(cursor, session_id: str, user_id: str) -> bool:
    """检查会话是否存在且属于指定用户"""
    cursor.execute("SELECT 1 FROM user_sessions WHERE session_id = %s AND user_id = %s", (session_id, user_id))
    return cursor.fetchone() is not None


@tool
def add_tasks(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """添加一个或多个新任务到任务列表中。
    
    可以添加单个任务或一次添加多个任务。
    任务可以作为子任务或者在特定任务之后添加。
    适用于规划复杂的工作序列。

    Args:
        tasks: 任务列表，每个任务包含以下可能的字段：
            - id: 任务唯一标识符（可选，如果不提供会自动生成）
            - content: 任务内容
            - status: 任务状态 (PENDING, IN_PROGRESS, COMPLETE, CANCELLED, ERROR)
            - parent_task_id: 父任务ID（可选，用于创建子任务）

    Returns:
        包含操作结果的字典
    """
    try:
        # 从上下文获取user_id和session_id
        user_id = get_user_id()
        session_id = get_session_id()
        
        # 如果没有从上下文获取到，则使用默认值（仅用于测试）
        if not user_id:
            user_id = "123e4567-e89b-12d3-a456-426614174000"  # 默认测试用户ID
            
        if not session_id:
            session_id = "123e4567-e89b-12d3-a456-426614174001"  # 默认测试会话ID

        conn = _get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 检查用户是否存在（在生产环境中启用，测试环境中可以禁用）
        if not settings.debug and not _check_user_exists(cursor, user_id):
            cursor.close()
            conn.close()
            return {"status": "error", "message": f"User {user_id} does not exist"}
        
        # 如果提供了session_id，检查会话是否存在且属于该用户
        if session_id and not settings.debug and not _check_session_exists(cursor, session_id, user_id):
            cursor.close()
            conn.close()
            return {"status": "error", "message": f"Session {session_id} does not exist or does not belong to user {user_id}"}
        
        added_tasks = []
        for task in tasks:
            # 生成任务ID
            task_id = str(uuid4())
            
            # 获取任务参数
            content = task.get("content", "")
            status = task.get("status", "PENDING")
            parent_task_id = task.get("parent_task_id")
            
            # 插入任务到数据库
            cursor.execute("""
                INSERT INTO tasks (id, user_id, session_id, content, status, parent_task_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, user_id, session_id, content, status, parent_task_id, created_at, updated_at
            """, (
                task_id,
                user_id,
                session_id,
                content,
                status,
                parent_task_id,
                datetime.now(),
                datetime.now()
            ))
            
            inserted_task = dict(cursor.fetchone())
            inserted_task['created_at'] = inserted_task['created_at'].isoformat()
            inserted_task['updated_at'] = inserted_task['updated_at'].isoformat()
            added_tasks.append(inserted_task)
            
            logger.info(f"Added task {task_id} for user {user_id} in session {session_id}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "status": "success", 
            "message": f"Successfully added {len(added_tasks)} tasks for user {user_id} in session {session_id}", 
            "tasks": added_tasks
        }
    except Exception as e:
        logger.error(f"Error adding tasks: {str(e)}")
        return {"status": "error", "message": f"Failed to add tasks: {str(e)}"}


@tool
def update_tasks(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """更新一个或多个任务的属性（状态、内容等）
    
    可以更新单个任务或一次更新多个任务。
    主要用于在复杂工作序列中进行计划、跟踪进度和管理工作。
    
    注意：此工具不能用于添加新任务，添加新任务请使用 add_tasks

    Args:
        tasks: 要更新的任务列表，每个任务必须包含id字段，以及需要更新的字段：
            - id: 要更新的任务ID（必需）
            - content: 新的任务内容（可选）
            - status: 新的任务状态（可选，PENDING, IN_PROGRESS, COMPLETE, CANCELLED, ERROR）

    Returns:
        包含操作结果的字典
    """
    try:
        # 从上下文获取user_id和session_id
        user_id = get_user_id()
        session_id = get_session_id()
        
        # 如果没有从上下文获取到，则使用默认值（仅用于测试）
        if not user_id:
            user_id = "123e4567-e89b-12d3-a456-426614174000"  # 默认测试用户ID
            
        if not session_id:
            session_id = "123e4567-e89b-12d3-a456-426614174001"  # 默认测试会话ID

        conn = _get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 检查用户是否存在（在生产环境中启用，测试环境中可以禁用）
        if not settings.debug and not _check_user_exists(cursor, user_id):
            cursor.close()
            conn.close()
            return {"status": "error", "message": f"User {user_id} does not exist"}
        
        updated_tasks = []
        for task_update in tasks:
            if "id" not in task_update:
                cursor.close()
                conn.close()
                return {
                    "status": "error",
                    "message": "Each task must have an 'id' field"
                }
            
            task_id = task_update["id"]
            
            # 检查任务是否存在且属于该用户
            cursor.execute("""
                SELECT id FROM tasks WHERE id = %s AND user_id = %s
            """, (task_id, user_id))
            
            if not cursor.fetchone():
                cursor.close()
                conn.close()
                return {
                    "status": "error",
                    "message": f"Task with id {task_id} not found for user {user_id}"
                }
            
            # 构建更新语句
            update_fields = []
            update_values = []
            
            if "content" in task_update:
                update_fields.append("content = %s")
                update_values.append(task_update["content"])
                
            if "status" in task_update:
                update_fields.append("status = %s")
                update_values.append(task_update["status"])
                
            if "parent_task_id" in task_update:
                update_fields.append("parent_task_id = %s")
                update_values.append(task_update["parent_task_id"])
            
            # 添加更新时间
            update_fields.append("updated_at = %s")
            update_values.append(datetime.now())
            
            # 添加任务ID和用户ID到值列表
            update_values.extend([task_id, user_id])
            
            # 更新任务
            cursor.execute(f"""
                UPDATE tasks 
                SET {', '.join(update_fields)}
                WHERE id = %s AND user_id = %s
                RETURNING id, user_id, session_id, content, status, parent_task_id, created_at, updated_at
            """, update_values)
            
            updated_task = dict(cursor.fetchone())
            updated_task['created_at'] = updated_task['created_at'].isoformat()
            updated_task['updated_at'] = updated_task['updated_at'].isoformat()
            updated_tasks.append(updated_task)
            
            logger.info(f"Updated task {task_id} for user {user_id} in session {session_id}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "status": "success", 
            "message": f"Successfully updated {len(updated_tasks)} tasks for user {user_id} in session {session_id}", 
            "tasks": updated_tasks
        }
    except Exception as e:
        logger.error(f"Error updating tasks: {str(e)}")
        return {"status": "error", "message": f"Failed to update tasks: {str(e)}"}


@tool
def get_tasks(status: str = None) -> Dict[str, Any]:
    """获取任务列表
    
    可以根据状态筛选任务，或获取所有任务

    Args:
        status: 任务状态筛选器 (PENDING, IN_PROGRESS, COMPLETE, CANCELLED, ERROR)

    Returns:
        包含任务列表的字典
    """
    try:
        # 从上下文获取user_id和session_id
        user_id = get_user_id()
        session_id = get_session_id()
        
        # 如果没有从上下文获取到，则使用默认值（仅用于测试）
        if not user_id:
            user_id = "123e4567-e89b-12d3-a456-426614174000"  # 默认测试用户ID
            
        if not session_id:
            session_id = "123e4567-e89b-12d3-a456-426614174001"  # 默认测试会话ID

        conn = _get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 检查用户是否存在（在生产环境中启用，测试环境中可以禁用）
        if not settings.debug and not _check_user_exists(cursor, user_id):
            cursor.close()
            conn.close()
            return {"status": "error", "message": f"User {user_id} does not exist"}
        
        # 构建查询语句
        query = "SELECT id, user_id, session_id, content, status, parent_task_id, created_at, updated_at FROM tasks WHERE user_id = %s"
        params = [user_id]
        
        if session_id:
            query += " AND session_id = %s"
            params.append(session_id)
            
        if status:
            query += " AND status = %s"
            params.append(status)
            
        query += " ORDER BY created_at ASC"
        
        cursor.execute(query, params)
        tasks = cursor.fetchall()
        
        # 格式化时间
        formatted_tasks = []
        for task in tasks:
            task_dict = dict(task)
            task_dict['created_at'] = task_dict['created_at'].isoformat()
            task_dict['updated_at'] = task_dict['updated_at'].isoformat()
            formatted_tasks.append(task_dict)
        
        cursor.close()
        conn.close()
        
        logger.info(f"Retrieved {len(formatted_tasks)} tasks for user {user_id} in session {session_id}")
        
        return {
            "status": "success",
            "message": f"Successfully retrieved {len(formatted_tasks)} tasks for user {user_id} in session {session_id}",
            "tasks": formatted_tasks
        }
    except Exception as e:
        logger.error(f"Error retrieving tasks: {str(e)}")
        return {"status": "error", "message": f"Failed to retrieve tasks: {str(e)}"}


@tool
def delete_tasks(task_ids: List[str]) -> Dict[str, Any]:
    """删除一个或多个任务
    
    Args:
        task_ids: 要删除的任务ID列表

    Returns:
        包含操作结果的字典
    """
    try:
        # 从上下文获取user_id和session_id
        user_id = get_user_id()
        session_id = get_session_id()
        
        # 如果没有从上下文获取到，则使用默认值（仅用于测试）
        if not user_id:
            user_id = "123e4567-e89b-12d3-a456-426614174000"  # 默认测试用户ID
            
        if not session_id:
            session_id = "123e4567-e89b-12d3-a456-426614174001"  # 默认测试会话ID

        conn = _get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 检查用户是否存在（在生产环境中启用，测试环境中可以禁用）
        if not settings.debug and not _check_user_exists(cursor, user_id):
            cursor.close()
            conn.close()
            return {"status": "error", "message": f"User {user_id} does not exist"}
        
        deleted_count = 0
        for task_id in task_ids:
            # 删除任务（仅当任务属于该用户时）
            if session_id:
                cursor.execute("""
                    DELETE FROM tasks WHERE id = %s AND user_id = %s AND session_id = %s
                """, (task_id, user_id, session_id))
            else:
                cursor.execute("""
                    DELETE FROM tasks WHERE id = %s AND user_id = %s
                """, (task_id, user_id))
            
            deleted_count += cursor.rowcount
            logger.info(f"Deleted task {task_id} for user {user_id} in session {session_id}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Successfully deleted {deleted_count} tasks for user {user_id} in session {session_id}",
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"Error deleting tasks: {str(e)}")
        return {"status": "error", "message": f"Failed to delete tasks: {str(e)}"}