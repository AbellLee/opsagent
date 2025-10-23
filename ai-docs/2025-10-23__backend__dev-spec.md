# 后端开发规范制定 · backend · 2025-10-23

> 相关路径：docs/backend_development_spec.md

## 背景 / 目标

- 需求/问题：为OpsAgent项目建立统一的后端开发规范，确保代码风格、架构设计和实现方式的一致性，提高代码质量和可维护性
- 约束/边界：必须符合项目现有技术栈（Python/FastAPI/LangGraph/PostgreSQL），遵循Clean Architecture原则，不能破坏现有模块边界

## 方案摘要

- 核心思路：
  1. 建立分层架构规范（Router → Service → Repository）
  2. 明确各层职责和依赖方向
  3. 统一代码风格和命名规范
- 影响面：
  - 代码：所有后端Python代码
  - 配置：无
  - 脚本：无

## 变更清单（按文件分组）

- `docs/backend_development_spec.md`
  - 变更点：创建完整的后端开发规范文档
  - 片段/伪代码/要点：
    ```md
    # 主要内容包括：
    - 适用范围与优先级
    - 核心原则（Clean Architecture等）
    - 目录结构规范
    - 技术栈说明
    - 分层职责定义
    - 包管理与命名规范
    - 代码风格与注释要求
    - 错误处理与日志规范
    - 安全与输入验证要求
    - 数据访问规范
    - 异步模型规范
    - HTTP约定
    - 代码模板示例
    - 生成规则（Must/Should/Must Not）
    - 测试与CI/CD要求
    - 文档与提交规范
    - 最小可行骨架示例
    ```

## 指令与运行

```bash
# 无特定命令行指令，该文档为规范性文档
```