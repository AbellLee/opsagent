# OpsAgent 项目重构方案

## 一、重构目标

### 1.1 核心目标
1. **Dify API 完全兼容**：确保聊天接口完全兼容 Dify 的 API 规范
2. **多模型支持**：允许用户自由选择和配置不同的 LLM 模型
3. **模型配置管理**：提供完整的模型配置 CRUD 功能
4. **向后兼容**：保持现有功能正常运行

### 1.2 参考项目
- 参考项目：https://github.com/lkpAgent/openAgent.git
- 主要借鉴：
  - LLM 配置管理模块
  - 多模型选择机制
  - Dify API 兼容实现

## 二、现状分析

### 2.1 当前架构
```
app/
├── api/
│   ├── deps.py             # 依赖注入（使用 psycopg2 原生连接）
│   └── routes/
│       ├── dify.py          # 已有 Dify 兼容接口
│       ├── agent.py         # Agent 聊天接口
│       ├── sessions.py      # 会话管理
│       ├── users.py         # 用户管理
│       ├── tools.py         # 工具管理
│       ├── tasks.py         # 任务管理
│       ├── approvals.py     # 审批管理
│       ├── interrupts.py    # 中断管理
│       └── mcp_config.py    # MCP 配置
├── core/
│   ├── llm.py              # LLM 初始化（单一模型）
│   ├── config.py           # 配置管理
│   ├── logger.py           # 日志配置
│   ├── instances.py        # 实例管理
│   └── user_context.py     # 用户上下文
├── models/
│   └── schemas.py          # Pydantic 数据模型（单文件）
├── services/
│   ├── agent/
│   │   ├── handlers.py     # 聊天处理逻辑
│   │   ├── tool_manager.py # 工具管理
│   │   ├── tool_approval.py # 工具审批
│   │   ├── interrupt_service.py # 中断服务
│   │   └── utils.py        # 工具函数
│   └── mcp/
│       └── config_service.py # MCP 配置服务
├── agent/
│   ├── graph.py            # LangGraph 图定义
│   ├── state.py            # Agent 状态
│   └── tools/              # Agent 工具
└── init_db.py              # 数据库初始化（使用原生 SQL）
```

### 2.2 当前技术栈特点
1. **数据库访问**：使用 `psycopg2` 原生连接，**没有使用 ORM**（如 SQLAlchemy）
2. **数据库操作**：直接使用原生 SQL 语句
3. **数据模型**：只有 Pydantic 模型用于 API 验证，没有数据库模型
4. **检查点存储**：使用 LangGraph 的 `PostgresSaver` 和 `PostgresStore`
5. **依赖注入**：通过 `get_db()` 返回 psycopg2 连接对象

### 2.3 存在的问题
1. **模型配置硬编码**：LLM 类型和配置通过环境变量固定
2. **缺少模型管理**：无法动态添加、修改、删除模型配置
3. **用户无法选择模型**：聊天时无法指定使用哪个模型
4. **Dify API 不完整**：缺少模型选择参数
5. **数据访问层混乱**：SQL 语句分散在各个路由文件中，难以维护
6. **缺少数据库迁移工具**：表结构变更需要手动修改 `init_db.py`
7. **schemas.py 过大**：所有 Pydantic 模型都在一个文件中

## 三、重构方案

### 3.0 技术选型决策

#### 3.0.1 数据库访问层选择

**当前状态**：项目使用 `psycopg2` 原生连接，没有使用 ORM

**方案对比**：

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **保持 psycopg2 原生** | 1. 性能最优<br>2. 无需学习 ORM<br>3. 与现有代码一致<br>4. 灵活性高 | 1. SQL 分散难维护<br>2. 缺少类型安全<br>3. 手动处理关系<br>4. 迁移管理困难 | ⭐⭐⭐ |
| **引入 SQLAlchemy ORM** | 1. 类型安全<br>2. 自动关系管理<br>3. 迁移工具（Alembic）<br>4. 代码更简洁 | 1. 学习成本<br>2. 性能略低<br>3. 需要重构现有代码<br>4. 增加依赖 | ⭐⭐⭐⭐ |
| **混合方案** | 1. 新功能用 ORM<br>2. 旧功能保持原生<br>3. 渐进式迁移 | 1. 代码风格不统一<br>2. 维护复杂度高 | ⭐⭐ |

**推荐方案**：**引入 SQLAlchemy ORM + Alembic**

**理由**：
1. **长期可维护性**：ORM 提供更好的代码组织和类型安全
2. **迁移管理**：Alembic 可以自动管理数据库版本和迁移
3. **与参考项目一致**：openAgent 使用 SQLAlchemy，便于借鉴
4. **渐进式迁移**：可以先用于新功能（LLM 配置），逐步迁移旧代码

**实施策略**：
- **第一阶段**：新增的 LLM 配置模块使用 SQLAlchemy
- **第二阶段**：保持现有模块使用 psycopg2（向后兼容）
- **第三阶段**（可选）：逐步迁移现有模块到 SQLAlchemy

#### 3.0.2 数据库迁移工具

**选择**：**Alembic**（SQLAlchemy 官方迁移工具）

**优势**：
- 自动生成迁移脚本
- 版本控制和回滚
- 支持多环境（开发、测试、生产）
- 与 SQLAlchemy 无缝集成

#### 3.0.3 API 密钥加密方案

**选择**：**Fernet（对称加密）**

**理由**：
- Python 标准库 `cryptography` 支持
- 简单易用，性能好
- 可逆加密（需要解密使用）
- 足够安全（AES-128）

**替代方案**：
- **环境变量 + 密钥管理服务**（AWS KMS、HashiCorp Vault）- 适合生产环境
- **非对称加密**（RSA）- 过于复杂，性能较差

### 3.1 数据库设计

#### 3.1.1 新增表：llm_configs（LLM 配置表）

**SQLAlchemy 模型定义**：
```python
# app/models/database/llm_config.py
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, TIMESTAMP, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from .base import Base

class LLMConfig(Base):
    __tablename__ = "llm_configs"

    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 基本信息
    name = Column(String(100), nullable=False, unique=True, comment="配置名称")
    provider = Column(String(50), nullable=False, comment="服务商")
    model_name = Column(String(100), nullable=False, comment="模型名称")
    api_key = Column(String(500), nullable=True, comment="API密钥（加密存储）")
    base_url = Column(String(200), nullable=True, comment="API基础URL")

    # 模型参数
    max_tokens = Column(Integer, default=2048, nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    top_p = Column(Float, default=1.0, nullable=False)
    frequency_penalty = Column(Float, default=0.0, nullable=False)
    presence_penalty = Column(Float, default=0.0, nullable=False)

    # 配置信息
    description = Column(Text, nullable=True, comment="配置描述")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    is_default = Column(Boolean, default=False, nullable=False, comment="是否为默认配置")
    is_embedding = Column(Boolean, default=False, nullable=False, comment="是否为嵌入模型")

    # 扩展配置
    extra_config = Column(JSONB, nullable=True, comment="额外配置参数")

    # 使用统计
    usage_count = Column(Integer, default=0, nullable=False, comment="使用次数")
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True, comment="最后使用时间")

    # 审计字段
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # 约束
    __table_args__ = (
        CheckConstraint(
            "provider IN ('openai', 'deepseek', 'tongyi', 'ollama', 'vllm', 'doubao', 'zhipu', 'moonshot', 'baidu')",
            name="check_provider"
        ),
        Index("idx_llm_configs_provider", "provider"),
        Index("idx_llm_configs_is_active", "is_active"),
        Index("idx_llm_configs_is_default_embedding", "is_default", "is_embedding"),
    )

    def __repr__(self):
        return f"<LLMConfig(id={self.id}, name='{self.name}', provider='{self.provider}')>"
```

**对应的 SQL（由 Alembic 自动生成）**：
```sql
CREATE TABLE llm_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    api_key VARCHAR(500),
    base_url VARCHAR(200),
    max_tokens INTEGER DEFAULT 2048 NOT NULL,
    temperature FLOAT DEFAULT 0.7 NOT NULL,
    top_p FLOAT DEFAULT 1.0 NOT NULL,
    frequency_penalty FLOAT DEFAULT 0.0 NOT NULL,
    presence_penalty FLOAT DEFAULT 0.0 NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    is_embedding BOOLEAN DEFAULT FALSE NOT NULL,
    extra_config JSONB,
    usage_count INTEGER DEFAULT 0 NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by UUID,
    updated_by UUID,
    CONSTRAINT check_provider CHECK (provider IN ('openai', 'deepseek', 'tongyi', 'ollama', 'vllm', 'doubao', 'zhipu', 'moonshot', 'baidu'))
);

CREATE INDEX idx_llm_configs_provider ON llm_configs(provider);
CREATE INDEX idx_llm_configs_is_active ON llm_configs(is_active);
CREATE INDEX idx_llm_configs_is_default_embedding ON llm_configs(is_default, is_embedding);
```

#### 3.1.2 修改表：user_sessions（会话表）
```sql
-- 添加字段
ALTER TABLE user_sessions ADD COLUMN llm_config_id UUID REFERENCES llm_configs(id);
ALTER TABLE user_sessions ADD COLUMN model_parameters JSONB;  -- 会话级别的模型参数覆盖
```

#### 3.1.3 修改表：conversations（对话表 - 如果存在）
```sql
-- 添加字段
ALTER TABLE conversations ADD COLUMN llm_config_id UUID REFERENCES llm_configs(id);
```

### 3.2 依赖管理

#### 3.2.1 新增 Python 依赖

**需要添加到 requirements.txt**：
```txt
# ORM 和数据库迁移
sqlalchemy>=2.0.0
alembic>=1.12.0

# 加密
cryptography>=41.0.0

# 现有依赖保持不变
psycopg2-binary>=2.9.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
langchain>=0.1.0
langchain-openai>=0.0.5
langgraph>=0.0.20
langgraph-checkpoint-postgres>=1.0.0
```

**开发依赖（requirements-dev.txt）**：
```txt
# 测试
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.25.0  # FastAPI 测试客户端

# 代码质量
black>=23.0.0
flake8>=6.0.0
mypy>=1.5.0
isort>=5.12.0

# 数据库工具
pgcli>=3.5.0  # PostgreSQL CLI
```

### 3.3 后端模块设计

#### 3.3.1 数据库基础层（app/db/）

**新增文件：app/db/base.py**
```python
"""SQLAlchemy 基础配置"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # 连接池预检查
    pool_size=10,        # 连接池大小
    max_overflow=20,     # 最大溢出连接数
    echo=settings.debug  # 开发环境打印 SQL
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

def get_db_session():
    """获取数据库会话（用于 SQLAlchemy）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**新增文件：app/db/session.py**
```python
"""数据库会话管理（兼容现有 psycopg2 和新的 SQLAlchemy）"""
from typing import Generator
import psycopg2
import psycopg2.extras
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logger import logger
from .base import SessionLocal

def get_db_psycopg2() -> Generator:
    """获取 psycopg2 原生连接（保持向后兼容）"""
    conn = None
    try:
        conn = psycopg2.connect(settings.database_url)
        psycopg2.extras.register_uuid(conn_or_curs=conn)
        yield conn
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_db_sqlalchemy() -> Generator[Session, None, None]:
    """获取 SQLAlchemy 会话（用于新功能）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 别名，方便使用
get_db = get_db_psycopg2  # 默认使用 psycopg2（向后兼容）
get_db_orm = get_db_sqlalchemy  # 新功能使用 ORM
```

**新增文件：app/db/repositories/base.py**
```python
"""基础 Repository 类"""
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    """基础数据访问类"""

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: any) -> Optional[ModelType]:
        """根据 ID 获取单条记录"""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """获取所有记录"""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: dict) -> ModelType:
        """创建记录"""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: any, obj_in: dict) -> Optional[ModelType]:
        """更新记录"""
        db_obj = self.get(id)
        if db_obj:
            for field, value in obj_in.items():
                setattr(db_obj, field, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: any) -> bool:
        """删除记录"""
        db_obj = self.get(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
```

**新增文件：app/db/repositories/llm_config.py**
```python
"""LLM 配置数据访问层"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.database.llm_config import LLMConfig
from .base import BaseRepository

class LLMConfigRepository(BaseRepository[LLMConfig]):
    """LLM 配置 Repository"""

    def __init__(self, db: Session):
        super().__init__(LLMConfig, db)

    def get_by_name(self, name: str) -> Optional[LLMConfig]:
        """根据名称获取配置"""
        return self.db.query(LLMConfig).filter(LLMConfig.name == name).first()

    def get_active_configs(self, is_embedding: Optional[bool] = None) -> List[LLMConfig]:
        """获取所有激活的配置"""
        query = self.db.query(LLMConfig).filter(LLMConfig.is_active == True)
        if is_embedding is not None:
            query = query.filter(LLMConfig.is_embedding == is_embedding)
        return query.all()

    def get_default_config(self, is_embedding: bool = False) -> Optional[LLMConfig]:
        """获取默认配置"""
        return self.db.query(LLMConfig).filter(
            and_(
                LLMConfig.is_default == True,
                LLMConfig.is_embedding == is_embedding,
                LLMConfig.is_active == True
            )
        ).first()

    def set_default(self, config_id: str, is_embedding: bool = False) -> bool:
        """设置默认配置"""
        # 取消同类型的其他默认配置
        self.db.query(LLMConfig).filter(
            LLMConfig.is_embedding == is_embedding
        ).update({"is_default": False})

        # 设置新的默认配置
        config = self.get(config_id)
        if config:
            config.is_default = True
            self.db.commit()
            return True
        return False

    def increment_usage(self, config_id: str):
        """增加使用次数"""
        from sqlalchemy import func
        config = self.get(config_id)
        if config:
            config.usage_count += 1
            config.last_used_at = func.now()
            self.db.commit()
```

#### 3.3.2 数据模型层（app/models/）

**新增文件：app/models/database/base.py**
```python
"""SQLAlchemy Base"""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
```

**新增文件：app/models/database/llm_config.py**
（见 3.1.1 节的 SQLAlchemy 模型定义）

**新增文件：app/models/schemas/llm_config.py**
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class LLMConfigBase(BaseModel):
    """LLM配置基础模型"""
    name: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., description="服务商")
    model_name: str = Field(..., description="模型名称")
    api_key: Optional[str] = Field(None, description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    max_tokens: int = Field(default=2048, ge=1, le=32000)
    temperature: float = Field(default=0.7, ge=0, le=2)
    top_p: float = Field(default=1.0, ge=0, le=1)
    frequency_penalty: float = Field(default=0.0, ge=-2, le=2)
    presence_penalty: float = Field(default=0.0, ge=-2, le=2)
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    is_default: bool = Field(default=False)
    is_embedding: bool = Field(default=False)
    extra_config: Optional[Dict[str, Any]] = None

class LLMConfigCreate(LLMConfigBase):
    """创建LLM配置"""
    pass

class LLMConfigUpdate(BaseModel):
    """更新LLM配置"""
    name: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    is_embedding: Optional[bool] = None
    extra_config: Optional[Dict[str, Any]] = None

class LLMConfigResponse(LLMConfigBase):
    """LLM配置响应"""
    id: UUID
    usage_count: int
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    api_key_masked: Optional[str] = None  # 脱敏后的API密钥

    class Config:
        from_attributes = True
```

**修改文件：app/models/schemas.py**
```python
# 添加到现有文件

class DifyChatRequest(BaseModel):
    """Dify聊天请求模型（增强版）"""
    inputs: Optional[Dict[str, Any]] = Field(default_factory=dict)
    query: str = Field(..., description="用户输入的消息内容")
    response_mode: str = Field(default="blocking", description="响应模式")
    conversation_id: Optional[str] = Field(None, description="会话ID")
    user: str = Field(..., description="用户标识")
    files: Optional[List[Dict[str, Any]]] = Field(None, description="上传的文件列表")
    
    # 新增：模型选择参数
    model_config_id: Optional[str] = Field(None, description="LLM配置ID")
    model: Optional[str] = Field(None, description="模型名称（兼容参数）")
    
    # 新增：模型参数覆盖
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1, le=32000)
    top_p: Optional[float] = Field(None, ge=0, le=1)

class AgentChatRequest(BaseModel):
    """Agent聊天请求模型（增强版）"""
    message: str
    response_mode: str = Field(default="blocking")
    tools: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None
    
    # 新增：模型选择参数
    model_config_id: Optional[str] = Field(None, description="LLM配置ID")
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1, le=32000)
```

#### 3.2.2 服务层（app/services/）

**新增文件：app/services/llm_service.py**
```python
from typing import Optional, Tuple, Any
from uuid import UUID
from app.core.logger import logger
from app.models.llm_config import LLMConfigResponse

class LLMService:
    """LLM服务，负责模型配置管理和模型实例化"""
    
    def __init__(self, db):
        self.db = db
    
    def get_llm_config(self, config_id: UUID) -> Optional[LLMConfigResponse]:
        """获取LLM配置"""
        pass
    
    def get_default_llm_config(self, is_embedding: bool = False) -> Optional[LLMConfigResponse]:
        """获取默认LLM配置"""
        pass
    
    def get_active_llm_configs(self, is_embedding: bool = False) -> list:
        """获取所有激活的LLM配置"""
        pass
    
    def create_llm_instance(self, config: LLMConfigResponse, **overrides) -> Tuple[Any, Optional[Any]]:
        """根据配置创建LLM实例"""
        pass
    
    def increment_usage(self, config_id: UUID):
        """增加使用次数"""
        pass
```

**修改文件：app/core/llm.py**
```python
# 重构为支持动态配置的版本
def create_llm_from_config(config: LLMConfigResponse, **overrides):
    """根据配置创建LLM实例"""
    # 实现逻辑
    pass
```

#### 3.2.3 API路由层（app/api/routes/）

**新增文件：app/api/routes/llm_configs.py**
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from uuid import UUID

router = APIRouter(prefix="/api/llm-configs", tags=["LLM配置"])

@router.get("/", response_model=List[LLMConfigResponse])
async def list_llm_configs(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    is_embedding: Optional[bool] = None,
    db = Depends(get_db)
):
    """获取LLM配置列表"""
    pass

@router.get("/default", response_model=LLMConfigResponse)
async def get_default_config(
    is_embedding: bool = False,
    db = Depends(get_db)
):
    """获取默认配置"""
    pass

@router.post("/", response_model=LLMConfigResponse)
async def create_llm_config(
    config: LLMConfigCreate,
    db = Depends(get_db)
):
    """创建LLM配置"""
    pass

@router.put("/{config_id}", response_model=LLMConfigResponse)
async def update_llm_config(
    config_id: UUID,
    config: LLMConfigUpdate,
    db = Depends(get_db)
):
    """更新LLM配置"""
    pass

@router.delete("/{config_id}")
async def delete_llm_config(
    config_id: UUID,
    db = Depends(get_db)
):
    """删除LLM配置"""
    pass

@router.post("/{config_id}/set-default")
async def set_default_config(
    config_id: UUID,
    db = Depends(get_db)
):
    """设置为默认配置"""
    pass
```

**修改文件：app/api/routes/dify.py**
```python
# 增强 Dify API 以支持模型选择

@router.post("/v1/chat-messages", response_model=DifyChatResponse)
async def chat_messages(
    request: DifyChatRequest,
    db = Depends(get_db)
):
    """
    Dify兼容的聊天消息接口（增强版）
    支持模型选择和参数覆盖
    """
    # 1. 确定使用的模型配置
    llm_service = LLMService(db)
    
    if request.model_config_id:
        # 使用指定的配置
        llm_config = llm_service.get_llm_config(UUID(request.model_config_id))
    elif request.model:
        # 根据模型名称查找配置
        llm_config = llm_service.find_config_by_model_name(request.model)
    else:
        # 使用默认配置
        llm_config = llm_service.get_default_llm_config()
    
    # 2. 应用参数覆盖
    model_params = {}
    if request.temperature is not None:
        model_params['temperature'] = request.temperature
    if request.max_tokens is not None:
        model_params['max_tokens'] = request.max_tokens
    if request.top_p is not None:
        model_params['top_p'] = request.top_p
    
    # 3. 创建LLM实例
    llm, _ = llm_service.create_llm_instance(llm_config, **model_params)
    
    # 4. 执行聊天逻辑（使用指定的LLM）
    # ... 现有逻辑
```

### 3.3 前端模块设计

#### 3.3.1 新增页面/组件

**1. LLM配置管理页面**
- 路径：`frontend/src/views/LLMConfigManagement.vue`
- 功能：
  - 配置列表展示（表格）
  - 新增配置（对话框）
  - 编辑配置（对话框）
  - 删除配置（确认）
  - 设置默认配置
  - 启用/禁用配置
  - 测试配置连接

**2. 模型选择组件**
- 路径：`frontend/src/components/ModelSelector.vue`
- 功能：
  - 下拉选择可用模型
  - 显示模型信息（provider、参数等）
  - 支持参数覆盖（temperature、max_tokens等）

**3. 聊天界面增强**
- 修改：`frontend/src/views/Chat.vue`
- 新增功能：
  - 会话级别的模型选择
  - 单次对话的模型选择
  - 模型参数调整面板

#### 3.3.2 API 服务封装

**新增文件：frontend/src/api/llmConfig.js**
```javascript
import request from '@/utils/request'

export function getLLMConfigs(params) {
  return request({
    url: '/api/llm-configs',
    method: 'get',
    params
  })
}

export function getDefaultLLMConfig(isEmbedding = false) {
  return request({
    url: '/api/llm-configs/default',
    method: 'get',
    params: { is_embedding: isEmbedding }
  })
}

export function createLLMConfig(data) {
  return request({
    url: '/api/llm-configs',
    method: 'post',
    data
  })
}

export function updateLLMConfig(id, data) {
  return request({
    url: `/api/llm-configs/${id}`,
    method: 'put',
    data
  })
}

export function deleteLLMConfig(id) {
  return request({
    url: `/api/llm-configs/${id}`,
    method: 'delete'
  })
}

export function setDefaultLLMConfig(id) {
  return request({
    url: `/api/llm-configs/${id}/set-default`,
    method: 'post'
  })
}
```

### 3.4 数据迁移方案

#### 3.4.1 迁移脚本

**新增文件：app/migrations/add_llm_configs.py**
```python
"""
添加LLM配置表和相关字段
"""
import os
from app.core.config import settings

def upgrade():
    """升级数据库"""
    # 1. 创建 llm_configs 表
    # 2. 添加 user_sessions.llm_config_id 字段
    # 3. 从环境变量创建默认配置

    # 读取当前环境变量配置
    llm_type = os.getenv("LLM_TYPE", "tongyi")
    llm_api_key = os.getenv("LLM_API_KEY")
    llm_model = os.getenv("LLM_MODEL")
    llm_base_url = os.getenv("LLM_BASE_URL")

    # 创建默认配置
    default_config = {
        "name": f"默认{llm_type}配置",
        "provider": llm_type,
        "model_name": llm_model or get_default_model(llm_type),
        "api_key": llm_api_key,
        "base_url": llm_base_url,
        "is_default": True,
        "is_active": True
    }

    # 插入数据库
    # ...

def downgrade():
    """降级数据库"""
    # 1. 删除 user_sessions.llm_config_id 字段
    # 2. 删除 llm_configs 表
    pass
```

#### 3.4.2 初始化数据

**修改文件：app/init_db.py**
```python
# 添加初始化LLM配置的逻辑

def init_default_llm_configs():
    """初始化默认LLM配置"""
    configs = [
        {
            "name": "通义千问-默认",
            "provider": "tongyi",
            "model_name": "qwen-turbo",
            "is_default": True,
            "is_active": True,
            "description": "阿里云通义千问默认配置"
        },
        # 可以添加更多预设配置
    ]

    for config_data in configs:
        # 检查是否已存在
        # 不存在则创建
        pass
```

## 四、实施步骤

### 4.1 第一阶段：环境准备和数据库层（1-2天）

**任务清单：**
- [ ] 安装新依赖（SQLAlchemy、Alembic、cryptography）
- [ ] 初始化 Alembic 配置
- [ ] 创建数据库基础层（`app/db/base.py`、`app/db/session.py`）
- [ ] 创建 SQLAlchemy Base 模型（`app/models/database/base.py`）
- [ ] 创建 LLM 配置数据库模型（`app/models/database/llm_config.py`）
- [ ] 创建 LLM 配置 Pydantic 模型（`app/models/schemas/llm_config.py`）
- [ ] 创建 Repository 层（`app/db/repositories/base.py`、`llm_config.py`）
- [ ] 生成 Alembic 迁移脚本
- [ ] 测试数据库迁移

**交付物：**
- `alembic.ini` - Alembic 配置文件
- `app/db/` - 数据库层目录
- `app/models/database/` - ORM 模型目录
- `app/models/schemas/llm_config.py` - Pydantic 模型
- `app/db/repositories/` - Repository 层
- `migrations/versions/xxx_add_llm_configs.py` - 迁移脚本
- 测试用例

**详细步骤**：

1. **安装依赖**
```bash
pip install sqlalchemy alembic cryptography
pip freeze > requirements.txt
```

2. **初始化 Alembic**
```bash
cd app
alembic init migrations
```

3. **配置 Alembic**（编辑 `alembic.ini` 和 `migrations/env.py`）

4. **创建数据库模型和 Repository**

5. **生成迁移脚本**
```bash
alembic revision --autogenerate -m "add llm_configs table"
```

6. **执行迁移**
```bash
alembic upgrade head
```

### 4.2 第二阶段：服务层重构（2-3天）

**任务清单：**
- [ ] 创建 LLMService 服务类
- [ ] 重构 `app/core/llm.py` 支持动态配置
- [ ] 修改 Agent handlers 支持模型选择
- [ ] 修改 Dify API 路由支持模型选择
- [ ] 向后兼容性测试

**交付物：**
- `app/services/llm_service.py`
- 修改后的 `app/core/llm.py`
- 修改后的 `app/services/agent/handlers.py`
- 修改后的 `app/api/routes/dify.py`
- 集成测试用例

### 4.3 第三阶段：API 路由层（1-2天）

**任务清单：**
- [ ] 创建 LLM 配置管理 API
- [ ] 增强 Dify API 支持模型选择
- [ ] 增强 Agent API 支持模型选择
- [ ] API 文档更新
- [ ] API 测试

**交付物：**
- `app/api/routes/llm_configs.py`
- 修改后的 `app/api/routes/dify.py`
- 修改后的 `app/api/routes/agent.py`
- API 文档
- Postman/测试脚本

### 4.4 第四阶段：前端开发（3-4天）

**任务清单：**
- [ ] 创建 LLM 配置管理页面
- [ ] 创建模型选择组件
- [ ] 修改聊天界面集成模型选择
- [ ] API 服务封装
- [ ] 前端测试

**交付物：**
- `frontend/src/views/LLMConfigManagement.vue`
- `frontend/src/components/ModelSelector.vue`
- 修改后的 `frontend/src/views/Chat.vue`
- `frontend/src/api/llmConfig.js`
- 前端测试用例

### 4.5 第五阶段：集成测试和文档（1-2天）

**任务清单：**
- [ ] 端到端测试
- [ ] 性能测试
- [ ] 安全测试（API密钥加密等）
- [ ] 用户文档编写
- [ ] 部署文档更新

**交付物：**
- 测试报告
- 用户使用文档
- 部署升级指南
- API 文档

## 五、技术细节

### 5.1 API 密钥安全

**加密存储方案：**
```python
from cryptography.fernet import Fernet
import os

class APIKeyEncryption:
    def __init__(self):
        # 从环境变量读取加密密钥
        self.key = os.getenv("ENCRYPTION_KEY").encode()
        self.cipher = Fernet(self.key)

    def encrypt(self, api_key: str) -> str:
        """加密API密钥"""
        return self.cipher.encrypt(api_key.encode()).decode()

    def decrypt(self, encrypted_key: str) -> str:
        """解密API密钥"""
        return self.cipher.decrypt(encrypted_key.encode()).decode()
```

### 5.2 模型配置缓存

**缓存策略：**
```python
from functools import lru_cache
from datetime import datetime, timedelta

class LLMConfigCache:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)

    def get(self, config_id: str):
        """获取缓存的配置"""
        if config_id in self.cache:
            config, timestamp = self.cache[config_id]
            if datetime.now() - timestamp < self.cache_ttl:
                return config
        return None

    def set(self, config_id: str, config):
        """设置缓存"""
        self.cache[config_id] = (config, datetime.now())

    def invalidate(self, config_id: str = None):
        """清除缓存"""
        if config_id:
            self.cache.pop(config_id, None)
        else:
            self.cache.clear()
```

### 5.3 Dify API 完全兼容性

**兼容性检查清单：**
- [x] POST /v1/chat-messages（已实现）
- [x] GET /v1/conversations/{conversation_id}（已实现）
- [x] DELETE /v1/conversations/{conversation_id}（已实现）
- [ ] 模型选择参数支持
- [ ] 流式响应格式完全一致
- [ ] 错误响应格式一致
- [ ] 元数据格式一致

## 六、风险评估与应对

### 6.1 风险识别

| 风险项 | 影响程度 | 可能性 | 应对措施 |
|--------|----------|--------|----------|
| 数据库迁移失败 | 高 | 低 | 1. 充分测试迁移脚本<br>2. 备份数据库<br>3. 准备回滚方案 |
| 向后兼容性问题 | 高 | 中 | 1. 保留环境变量配置方式<br>2. 自动迁移现有配置<br>3. 充分的兼容性测试 |
| API密钥泄露 | 高 | 低 | 1. 加密存储<br>2. 访问控制<br>3. 审计日志 |
| 性能下降 | 中 | 中 | 1. 配置缓存<br>2. 数据库索引优化<br>3. 性能测试 |
| 前端兼容性 | 低 | 低 | 1. 渐进式增强<br>2. 浏览器兼容性测试 |

### 6.2 回滚方案

**数据库回滚：**
```bash
# 执行降级脚本
python app/migrations/add_llm_configs.py downgrade

# 恢复备份
pg_restore -d opsagent backup.sql
```

**代码回滚：**
```bash
# Git 回滚到重构前的版本
git revert <commit-hash>
```

## 七、验收标准

### 7.1 功能验收

- [ ] 可以通过界面创建、编辑、删除 LLM 配置
- [ ] 可以设置默认 LLM 配置
- [ ] 聊天时可以选择使用的模型
- [ ] Dify API 完全兼容，支持模型选择
- [ ] 原有功能正常运行（向后兼容）
- [ ] API 密钥安全存储和使用

### 7.2 性能验收

- [ ] 配置查询响应时间 < 100ms
- [ ] 聊天响应时间与重构前相当
- [ ] 数据库查询优化，无 N+1 问题
- [ ] 前端页面加载时间 < 2s

### 7.3 安全验收

- [ ] API 密钥加密存储
- [ ] API 密钥不在日志中明文显示
- [ ] 配置管理需要权限控制
- [ ] SQL 注入防护
- [ ] XSS 防护

## 八、后续优化建议

### 8.1 短期优化（1-2周）

1. **模型性能监控**
   - 记录每个模型的响应时间
   - 记录每个模型的成功率
   - 提供性能分析报表

2. **智能模型推荐**
   - 根据任务类型推荐合适的模型
   - 根据历史使用情况推荐

3. **成本控制**
   - 记录每个模型的 token 使用量
   - 提供成本统计报表
   - 设置使用配额

### 8.2 中期优化（1-2月）

1. **模型负载均衡**
   - 支持同一模型的多个配置
   - 自动负载均衡
   - 故障转移

2. **模型版本管理**
   - 支持模型配置版本控制
   - 配置变更历史记录
   - 配置回滚功能

3. **高级参数调优**
   - 提供参数调优建议
   - A/B 测试不同参数配置
   - 自动参数优化

### 8.3 长期优化（3-6月）

1. **多租户支持**
   - 租户级别的模型配置
   - 租户级别的配额管理
   - 租户级别的成本核算

2. **模型市场**
   - 预设模型配置模板
   - 社区分享配置
   - 配置评分和评论

3. **AI 辅助配置**
   - 根据需求自动推荐配置
   - 自动测试和验证配置
   - 智能参数调优

## 九、目录结构调整方案

### 9.1 当前目录结构问题

**存在的问题：**
1. **缺少数据库层**：没有独立的 database/repository 层，数据访问逻辑分散
2. **models 目录混乱**：只有 schemas.py，缺少数据库模型（ORM models）
3. **缺少 utils 目录**：工具函数分散在各个模块中
4. **缺少 middleware 目录**：中间件没有统一管理
5. **测试目录不完整**：缺少单元测试、集成测试的分类
6. **配置文件分散**：环境配置、应用配置混在一起
7. **前端目录可优化**：缺少 layouts、hooks 等现代前端结构

### 9.2 推荐的新目录结构

#### 9.2.1 后端目录结构（推荐）

```
opsagent/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI 应用入口
│   │
│   ├── api/                         # API 路由层
│   │   ├── __init__.py
│   │   ├── deps.py                  # 依赖注入
│   │   └── v1/                      # API 版本 v1
│   │       ├── __init__.py
│   │       ├── router.py            # 路由聚合
│   │       └── endpoints/           # 端点实现
│   │           ├── __init__.py
│   │           ├── agent.py         # Agent 聊天
│   │           ├── dify.py          # Dify 兼容接口
│   │           ├── sessions.py      # 会话管理
│   │           ├── users.py         # 用户管理
│   │           ├── llm_configs.py   # LLM 配置管理（新增）
│   │           ├── tools.py         # 工具管理
│   │           ├── tasks.py         # 任务管理
│   │           ├── approvals.py     # 审批管理
│   │           ├── interrupts.py    # 中断管理
│   │           └── mcp_config.py    # MCP 配置
│   │
│   ├── core/                        # 核心配置和基础设施
│   │   ├── __init__.py
│   │   ├── config.py                # 应用配置
│   │   ├── security.py              # 安全相关（加密、认证）
│   │   ├── logger.py                # 日志配置
│   │   ├── exceptions.py            # 自定义异常
│   │   ├── events.py                # 事件处理
│   │   └── constants.py             # 常量定义
│   │
│   ├── db/                          # 数据库层（新增）
│   │   ├── __init__.py
│   │   ├── base.py                  # 数据库基础配置
│   │   ├── session.py               # 数据库会话管理
│   │   ├── init_db.py               # 数据库初始化
│   │   └── repositories/            # 数据访问层（Repository 模式）
│   │       ├── __init__.py
│   │       ├── base.py              # 基础 Repository
│   │       ├── user.py              # 用户数据访问
│   │       ├── session.py           # 会话数据访问
│   │       ├── llm_config.py        # LLM 配置数据访问（新增）
│   │       ├── task.py              # 任务数据访问
│   │       └── mcp_config.py        # MCP 配置数据访问
│   │
│   ├── models/                      # 数据模型层
│   │   ├── __init__.py
│   │   ├── database/                # 数据库模型（ORM）（新增）
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # SQLAlchemy Base
│   │   │   ├── user.py              # 用户表模型
│   │   │   ├── session.py           # 会话表模型
│   │   │   ├── llm_config.py        # LLM 配置表模型（新增）
│   │   │   ├── task.py              # 任务表模型
│   │   │   ├── approval.py          # 审批表模型
│   │   │   └── mcp_config.py        # MCP 配置表模型
│   │   │
│   │   └── schemas/                 # Pydantic 模型（API 数据验证）
│   │       ├── __init__.py
│   │       ├── base.py              # 基础 Schema
│   │       ├── user.py              # 用户 Schema
│   │       ├── session.py           # 会话 Schema
│   │       ├── llm_config.py        # LLM 配置 Schema（新增）
│   │       ├── agent.py             # Agent Schema
│   │       ├── dify.py              # Dify Schema
│   │       ├── task.py              # 任务 Schema
│   │       ├── tool.py              # 工具 Schema
│   │       └── mcp.py               # MCP Schema
│   │
│   ├── services/                    # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── auth_service.py          # 认证服务
│   │   ├── user_service.py          # 用户服务
│   │   ├── session_service.py       # 会话服务
│   │   ├── llm_service.py           # LLM 服务（新增）
│   │   ├── agent/                   # Agent 相关服务
│   │   │   ├── __init__.py
│   │   │   ├── chat_service.py      # 聊天服务
│   │   │   ├── handlers.py          # 消息处理器
│   │   │   ├── tool_manager.py      # 工具管理
│   │   │   ├── tool_approval.py     # 工具审批
│   │   │   ├── interrupt_service.py # 中断服务
│   │   │   └── utils.py             # 工具函数
│   │   └── mcp/                     # MCP 相关服务
│   │       ├── __init__.py
│   │       └── config_service.py    # MCP 配置服务
│   │
│   ├── agent/                       # Agent 核心（LangGraph）
│   │   ├── __init__.py
│   │   ├── graph.py                 # Agent 图定义
│   │   ├── state.py                 # Agent 状态
│   │   ├── nodes/                   # 图节点（新增）
│   │   │   ├── __init__.py
│   │   │   ├── chat_node.py
│   │   │   ├── tool_node.py
│   │   │   └── approval_node.py
│   │   └── tools/                   # Agent 工具
│   │       ├── __init__.py
│   │       └── ...
│   │
│   ├── middleware/                  # 中间件（新增）
│   │   ├── __init__.py
│   │   ├── auth.py                  # 认证中间件
│   │   ├── cors.py                  # CORS 中间件
│   │   ├── logging.py               # 日志中间件
│   │   └── error_handler.py         # 错误处理中间件
│   │
│   ├── utils/                       # 工具函数（新增）
│   │   ├── __init__.py
│   │   ├── encryption.py            # 加密工具
│   │   ├── datetime.py              # 时间处理
│   │   ├── validators.py            # 验证器
│   │   └── helpers.py               # 辅助函数
│   │
│   └── migrations/                  # 数据库迁移（新增）
│       ├── __init__.py
│       ├── env.py                   # Alembic 环境配置
│       ├── script.py.mako           # 迁移脚本模板
│       └── versions/                # 迁移版本
│           └── ...
│
├── tests/                           # 测试目录（重构）
│   ├── __init__.py
│   ├── conftest.py                  # pytest 配置
│   ├── unit/                        # 单元测试
│   │   ├── __init__.py
│   │   ├── test_services/
│   │   ├── test_repositories/
│   │   └── test_utils/
│   ├── integration/                 # 集成测试
│   │   ├── __init__.py
│   │   ├── test_api/
│   │   └── test_agent/
│   └── e2e/                         # 端到端测试
│       ├── __init__.py
│       └── test_dify_api.py
│
├── scripts/                         # 脚本目录（新增）
│   ├── init_db.py                   # 初始化数据库
│   ├── seed_data.py                 # 种子数据
│   └── migrate.py                   # 迁移脚本
│
├── config/                          # 配置文件目录（新增）
│   ├── .env.example                 # 环境变量示例
│   ├── .env.development             # 开发环境配置
│   ├── .env.production              # 生产环境配置
│   └── logging.yaml                 # 日志配置
│
├── docs/                            # 文档目录
│   ├── README.md
│   ├── API.md                       # API 文档
│   ├── DEPLOYMENT.md                # 部署文档
│   ├── DEVELOPMENT.md               # 开发文档
│   ├── DIFY_API_COMPATIBILITY.md
│   ├── DIFY_INTEGRATION_SUMMARY.md
│   └── REFACTORING_PLAN.md
│
├── ai-docs/                         # AI 生成的文档
│   └── ...
│
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt                 # Python 依赖
├── requirements-dev.txt             # 开发依赖（新增）
├── pyproject.toml                   # Python 项目配置（新增）
├── alembic.ini                      # Alembic 配置（新增）
└── README.md
```

#### 9.2.2 前端目录结构（推荐）

```
frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
│
├── src/
│   ├── main.js                      # 应用入口
│   ├── App.vue                      # 根组件
│   │
│   ├── api/                         # API 服务层
│   │   ├── index.js                 # API 聚合
│   │   ├── request.js               # 请求封装（新增）
│   │   ├── auth.js                  # 认证 API（新增）
│   │   ├── session.js               # 会话 API（新增）
│   │   ├── agent.js                 # Agent API（新增）
│   │   ├── llmConfig.js             # LLM 配置 API（新增）
│   │   ├── tool.js                  # 工具 API（新增）
│   │   └── mcp.js                   # MCP API（新增）
│   │
│   ├── assets/                      # 静态资源
│   │   ├── images/
│   │   ├── icons/
│   │   └── fonts/
│   │
│   ├── components/                  # 组件目录
│   │   ├── common/                  # 通用组件（新增）
│   │   │   ├── Button.vue
│   │   │   ├── Input.vue
│   │   │   ├── Modal.vue
│   │   │   ├── Loading.vue
│   │   │   └── ...
│   │   ├── layout/                  # 布局组件（新增）
│   │   │   ├── AppHeader.vue
│   │   │   ├── AppSidebar.vue
│   │   │   ├── AppFooter.vue
│   │   │   └── UserMenu.vue
│   │   ├── chat/                    # 聊天相关组件（新增）
│   │   │   ├── ChatMessage.vue
│   │   │   ├── MessageInput.vue
│   │   │   ├── SessionList.vue
│   │   │   └── ModelSelector.vue    # 模型选择器（新增）
│   │   ├── task/                    # 任务相关组件（新增）
│   │   │   ├── TaskList.vue
│   │   │   ├── TaskItem.vue
│   │   │   └── ...
│   │   ├── llm/                     # LLM 配置组件（新增）
│   │   │   ├── LLMConfigList.vue
│   │   │   ├── LLMConfigForm.vue
│   │   │   └── LLMConfigCard.vue
│   │   └── mcp/                     # MCP 组件
│   │       ├── MCPConfigPanel.vue
│   │       └── ...
│   │
│   ├── views/                       # 页面视图
│   │   ├── auth/                    # 认证页面（新增）
│   │   │   ├── LoginView.vue
│   │   │   └── RegisterView.vue
│   │   ├── chat/                    # 聊天页面（新增）
│   │   │   └── ChatView.vue
│   │   ├── llm/                     # LLM 管理页面（新增）
│   │   │   └── LLMConfigManagement.vue
│   │   ├── settings/                # 设置页面（新增）
│   │   │   └── SettingsView.vue
│   │   └── WelcomeView.vue
│   │
│   ├── layouts/                     # 布局模板（新增）
│   │   ├── DefaultLayout.vue        # 默认布局
│   │   ├── AuthLayout.vue           # 认证布局
│   │   └── EmptyLayout.vue          # 空布局
│   │
│   ├── router/                      # 路由配置
│   │   ├── index.js                 # 路由主文件
│   │   ├── routes.js                # 路由定义（新增）
│   │   └── guards.js                # 路由守卫（新增）
│   │
│   ├── stores/                      # 状态管理（Pinia）
│   │   ├── index.js                 # Store 聚合（新增）
│   │   ├── user.js                  # 用户状态
│   │   ├── session.js               # 会话状态
│   │   ├── llmConfig.js             # LLM 配置状态（新增）
│   │   ├── chat.js                  # 聊天状态（新增）
│   │   └── app.js                   # 应用状态（新增）
│   │
│   ├── composables/                 # 组合式函数（Composition API）
│   │   ├── useAuth.js               # 认证逻辑（新增）
│   │   ├── useChat.js               # 聊天逻辑（新增）
│   │   ├── useLLMConfig.js          # LLM 配置逻辑（新增）
│   │   ├── useScrollManager.js      # 滚动管理
│   │   └── useWebSocket.js          # WebSocket（新增）
│   │
│   ├── utils/                       # 工具函数
│   │   ├── request.js               # HTTP 请求工具
│   │   ├── storage.js               # 本地存储工具（新增）
│   │   ├── validators.js            # 验证工具（新增）
│   │   ├── formatters.js            # 格式化工具（新增）
│   │   ├── markdown.js              # Markdown 处理
│   │   └── helpers.js               # 辅助函数（新增）
│   │
│   ├── styles/                      # 样式文件
│   │   ├── variables.css            # CSS 变量（新增）
│   │   ├── design-system.css        # 设计系统
│   │   ├── global.css               # 全局样式
│   │   └── themes/                  # 主题（新增）
│   │       ├── light.css
│   │       └── dark.css
│   │
│   ├── constants/                   # 常量定义
│   │   ├── index.js                 # 常量聚合（新增）
│   │   ├── messageTypes.js          # 消息类型
│   │   ├── apiEndpoints.js          # API 端点（新增）
│   │   └── config.js                # 配置常量（新增）
│   │
│   └── types/                       # TypeScript 类型定义（如果使用 TS）（新增）
│       ├── api.d.ts
│       ├── models.d.ts
│       └── ...
│
├── tests/                           # 前端测试（新增）
│   ├── unit/                        # 单元测试
│   │   └── ...
│   └── e2e/                         # E2E 测试
│       └── ...
│
├── .env.example                     # 环境变量示例
├── .env.development                 # 开发环境
├── .env.production                  # 生产环境
├── .eslintrc.js                     # ESLint 配置
├── .prettierrc                      # Prettier 配置
├── babel.config.js                  # Babel 配置
├── vue.config.js                    # Vue CLI 配置
├── webpack.config.js                # Webpack 配置
├── package.json
├── package-lock.json
└── README.md
```

### 9.3 目录调整实施步骤

#### 9.3.1 后端目录调整步骤

**第一步：创建新目录结构**
```bash
# 创建新目录
mkdir -p app/db/repositories
mkdir -p app/models/database
mkdir -p app/models/schemas
mkdir -p app/api/v1/endpoints
mkdir -p app/middleware
mkdir -p app/utils
mkdir -p app/migrations/versions
mkdir -p app/agent/nodes
mkdir -p scripts
mkdir -p config
mkdir -p tests/{unit,integration,e2e}
```

**第二步：迁移现有文件**
```bash
# 迁移 schemas
mv app/models/schemas.py app/models/schemas/__init__.py

# 迁移 API 路由
mkdir -p app/api/v1/endpoints
mv app/api/routes/* app/api/v1/endpoints/

# 迁移初始化脚本
mv app/init_db.py scripts/init_db.py
```

**第三步：拆分和重构文件**
- 将 `app/models/schemas.py` 拆分为多个文件
- 创建数据库模型文件
- 创建 Repository 层
- 提取工具函数到 utils

**第四步：更新导入路径**
- 全局搜索替换导入路径
- 更新 `__init__.py` 文件

#### 9.3.2 前端目录调整步骤

**第一步：创建新目录结构**
```bash
cd frontend/src
mkdir -p api
mkdir -p components/{common,layout,chat,task,llm,mcp}
mkdir -p views/{auth,chat,llm,settings}
mkdir -p layouts
mkdir -p composables
mkdir -p utils
mkdir -p stores
mkdir -p constants
mkdir -p styles/themes
```

**第二步：迁移现有文件**
```bash
# 迁移组件
mv components/AppHeader.vue components/layout/
mv components/AppSidebar.vue components/layout/
mv components/UserMenu.vue components/layout/
mv components/ChatMessage.vue components/chat/
mv components/MessageInput.vue components/chat/
mv components/SessionList.vue components/chat/
mv components/TaskList.vue components/task/
mv components/TaskItem.vue components/task/
mv components/MCPConfigPanel.vue components/mcp/

# 迁移视图
mkdir -p views/auth views/chat
mv views/LoginView.vue views/auth/
mv views/RegisterView.vue views/auth/
mv views/ChatView.vue views/chat/
```

**第三步：拆分 API 服务**
- 将 `api/index.js` 拆分为多个模块
- 创建独立的 API 服务文件

**第四步：创建布局组件**
- 创建 `DefaultLayout.vue`
- 创建 `AuthLayout.vue`
- 更新路由使用布局

### 9.4 目录调整的优势

**后端优势：**
1. **清晰的分层架构**：API → Service → Repository → Database
2. **更好的可测试性**：每层可独立测试
3. **更好的可维护性**：职责分离，易于定位问题
4. **更好的可扩展性**：新增功能只需在对应层添加
5. **符合最佳实践**：遵循 Clean Architecture 原则

**前端优势：**
1. **组件分类清晰**：按功能模块组织
2. **代码复用性高**：通用组件、Composables
3. **易于协作开发**：目录结构清晰，减少冲突
4. **性能优化**：按需加载，代码分割
5. **符合 Vue 3 最佳实践**：Composition API、Pinia

### 9.5 迁移注意事项

**重要提示：**
1. **逐步迁移**：不要一次性全部迁移，分模块进行
2. **保持测试**：每次迁移后运行测试确保功能正常
3. **更新文档**：及时更新开发文档和 README
4. **团队沟通**：确保团队成员了解新的目录结构
5. **版本控制**：使用 Git 分支进行迁移，便于回滚

**迁移顺序建议：**
1. 先创建新目录结构
2. 迁移工具函数和常量
3. 迁移数据模型
4. 迁移服务层
5. 迁移 API 层
6. 迁移前端组件
7. 更新测试
8. 更新文档

## 十、性能优化建议

### 10.1 数据库性能优化

**连接池配置**：
```python
# app/db/base.py
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,      # 连接健康检查
    pool_size=10,            # 连接池大小
    max_overflow=20,         # 最大溢出连接
    pool_recycle=3600,       # 连接回收时间（秒）
    echo=settings.debug      # SQL 日志
)
```

**查询优化**：
1. **使用索引**：已在表设计中添加关键索引
2. **延迟加载**：使用 `lazy='select'` 避免 N+1 查询
3. **批量操作**：使用 `bulk_insert_mappings` 批量插入
4. **查询缓存**：使用 Redis 缓存热点配置

**示例：配置缓存**
```python
# app/services/llm_service.py
from functools import lru_cache
from datetime import datetime, timedelta
import redis

class LLMConfigCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True
        )
        self.ttl = 300  # 5分钟

    def get_config(self, config_id: str):
        """从缓存获取配置"""
        key = f"llm_config:{config_id}"
        cached = self.redis_client.get(key)
        if cached:
            return json.loads(cached)
        return None

    def set_config(self, config_id: str, config: dict):
        """设置缓存"""
        key = f"llm_config:{config_id}"
        self.redis_client.setex(key, self.ttl, json.dumps(config))

    def invalidate(self, config_id: str = None):
        """清除缓存"""
        if config_id:
            self.redis_client.delete(f"llm_config:{config_id}")
        else:
            # 清除所有配置缓存
            keys = self.redis_client.keys("llm_config:*")
            if keys:
                self.redis_client.delete(*keys)
```

### 10.2 API 性能优化

**异步处理**：
```python
# 使用异步数据库操作
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

async_engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.debug
)

async def get_llm_config_async(config_id: str):
    async with AsyncSession(async_engine) as session:
        result = await session.execute(
            select(LLMConfig).where(LLMConfig.id == config_id)
        )
        return result.scalar_one_or_none()
```

**响应压缩**：
```python
# app/main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**分页优化**：
```python
# 使用游标分页代替偏移分页
def get_configs_cursor_pagination(cursor: Optional[str] = None, limit: int = 20):
    query = db.query(LLMConfig).filter(LLMConfig.is_active == True)
    if cursor:
        query = query.filter(LLMConfig.id > cursor)
    configs = query.order_by(LLMConfig.id).limit(limit + 1).all()

    has_next = len(configs) > limit
    if has_next:
        configs = configs[:limit]

    next_cursor = str(configs[-1].id) if has_next else None
    return configs, next_cursor
```

### 10.3 前端性能优化

**代码分割**：
```javascript
// router/index.js
const routes = [
  {
    path: '/llm-config',
    component: () => import(/* webpackChunkName: "llm-config" */ '@/views/llm/LLMConfigManagement.vue')
  }
]
```

**虚拟滚动**（大列表优化）：
```vue
<!-- 使用 vue-virtual-scroller -->
<template>
  <RecycleScroller
    :items="llmConfigs"
    :item-size="80"
    key-field="id"
  >
    <template #default="{ item }">
      <LLMConfigCard :config="item" />
    </template>
  </RecycleScroller>
</template>
```

**请求去重和缓存**：
```javascript
// composables/useLLMConfig.js
import { useQuery } from '@tanstack/vue-query'

export function useLLMConfigs() {
  return useQuery({
    queryKey: ['llmConfigs'],
    queryFn: () => getLLMConfigs(),
    staleTime: 5 * 60 * 1000, // 5分钟内不重新请求
    cacheTime: 10 * 60 * 1000 // 缓存10分钟
  })
}
```

## 十一、安全加固建议

### 11.1 API 密钥安全

**加密存储实现**：
```python
# app/utils/encryption.py
from cryptography.fernet import Fernet
import os
import base64

class APIKeyEncryption:
    def __init__(self):
        # 从环境变量读取加密密钥
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError("ENCRYPTION_KEY not set in environment")
        self.cipher = Fernet(key.encode())

    def encrypt(self, api_key: str) -> str:
        """加密 API 密钥"""
        if not api_key:
            return None
        return self.cipher.encrypt(api_key.encode()).decode()

    def decrypt(self, encrypted_key: str) -> str:
        """解密 API 密钥"""
        if not encrypted_key:
            return None
        return self.cipher.decrypt(encrypted_key.encode()).decode()

    @staticmethod
    def generate_key() -> str:
        """生成新的加密密钥"""
        return Fernet.generate_key().decode()

# 使用示例
encryption = APIKeyEncryption()

# 保存时加密
encrypted_key = encryption.encrypt(api_key)
config.api_key = encrypted_key

# 使用时解密
decrypted_key = encryption.decrypt(config.api_key)
```

**密钥脱敏**：
```python
# app/models/schemas/llm_config.py
class LLMConfigResponse(LLMConfigBase):
    id: UUID
    api_key_masked: Optional[str] = None

    @classmethod
    def from_orm(cls, obj):
        """从 ORM 对象创建响应模型"""
        data = obj.__dict__.copy()
        # 脱敏 API 密钥
        if data.get('api_key'):
            data['api_key_masked'] = cls.mask_api_key(data['api_key'])
            data.pop('api_key')  # 不返回原始密钥
        return cls(**data)

    @staticmethod
    def mask_api_key(api_key: str) -> str:
        """脱敏 API 密钥"""
        if not api_key or len(api_key) < 8:
            return "****"
        return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"
```

### 11.2 权限控制

**基于角色的访问控制（RBAC）**：
```python
# app/core/security.py
from enum import Enum
from fastapi import Depends, HTTPException, status

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

def require_role(required_role: UserRole):
    """角色权限装饰器"""
    def role_checker(current_user = Depends(get_current_user)):
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        return current_user
    return role_checker

# 使用示例
@router.post("/llm-configs")
async def create_llm_config(
    config: LLMConfigCreate,
    current_user = Depends(require_role(UserRole.ADMIN))
):
    """只有管理员可以创建配置"""
    pass
```

### 11.3 输入验证和 SQL 注入防护

**使用 Pydantic 验证**：
```python
# app/models/schemas/llm_config.py
from pydantic import BaseModel, Field, validator

class LLMConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, regex=r'^[a-zA-Z0-9_\-\u4e00-\u9fa5]+$')
    provider: str = Field(..., regex=r'^[a-z]+$')

    @validator('base_url')
    def validate_url(cls, v):
        """验证 URL 格式"""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('base_url must start with http:// or https://')
        return v

    @validator('temperature')
    def validate_temperature(cls, v):
        """验证温度参数"""
        if v < 0 or v > 2:
            raise ValueError('temperature must be between 0 and 2')
        return v
```

**ORM 自动防护 SQL 注入**：
使用 SQLAlchemy ORM 可以自动防止 SQL 注入，因为参数会被正确转义。

### 11.4 审计日志

**操作审计**：
```python
# app/models/database/audit_log.py
from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from .base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE
    resource_type = Column(String(50), nullable=False)  # llm_config, session, etc.
    resource_id = Column(String(100), nullable=False)
    changes = Column(JSONB, nullable=True)  # 变更内容
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

# 使用示例
def log_audit(db: Session, user_id: UUID, action: str, resource_type: str, resource_id: str, changes: dict = None):
    """记录审计日志"""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=changes
    )
    db.add(audit)
    db.commit()
```

## 十二、监控和可观测性

### 12.1 日志增强

**结构化日志**：
```python
# app/core/logger.py
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log(self, level: str, message: str, **kwargs):
        """结构化日志"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        self.logger.log(
            getattr(logging, level.upper()),
            json.dumps(log_data)
        )

    def info(self, message: str, **kwargs):
        self.log("info", message, **kwargs)

    def error(self, message: str, **kwargs):
        self.log("error", message, **kwargs)

# 使用示例
logger = StructuredLogger(__name__)
logger.info(
    "LLM config created",
    config_id=str(config.id),
    provider=config.provider,
    user_id=str(current_user.id)
)
```

### 12.2 性能监控

**API 响应时间监控**：
```python
# app/middleware/monitoring.py
import time
from fastapi import Request
from app.core.logger import logger

async def monitoring_middleware(request: Request, call_next):
    """监控中间件"""
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    logger.info(
        "API request",
        method=request.method,
        path=request.url.path,
        duration_ms=round(duration * 1000, 2),
        status_code=response.status_code
    )

    # 慢查询告警
    if duration > 1.0:  # 超过1秒
        logger.warning(
            "Slow API request",
            method=request.method,
            path=request.url.path,
            duration_ms=round(duration * 1000, 2)
        )

    return response
```

### 12.3 健康检查

**健康检查端点**：
```python
# app/api/v1/endpoints/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db_orm

router = APIRouter(prefix="/health", tags=["健康检查"])

@router.get("")
async def health_check(db: Session = Depends(get_db_orm)):
    """健康检查"""
    try:
        # 检查数据库连接
        db.execute("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

## 十三、总结

本重构方案旨在将 OpsAgent 项目升级为支持多模型选择和 Dify API 完全兼容的智能对话系统。通过引入 LLM 配置管理模块，用户可以灵活地添加、配置和选择不同的大语言模型，同时保持与现有系统的向后兼容性。

**核心价值：**
1. **灵活性**：支持多种 LLM 提供商和模型
2. **可扩展性**：易于添加新的模型配置
3. **兼容性**：完全兼容 Dify API 规范
4. **安全性**：API 密钥加密存储
5. **易用性**：友好的配置管理界面
6. **可维护性**：清晰的目录结构和分层架构

**预期收益：**
- 用户可以根据不同场景选择最合适的模型
- 降低对单一模型提供商的依赖
- 提高系统的灵活性和可维护性
- 完全兼容 Dify 生态系统
- 更好的代码组织和团队协作效率


