# 前端开发规范 · frontend · 2025-10-23
> 相关路径：frontend/src/、frontend/package.json

## 背景 / 目标
- 需求/问题：建立统一的前端开发规范，提高代码质量和团队协作效率
- 约束/边界：基于现有Vue3技术栈，适配当前项目结构

## 方案摘要
- 核心思路：
  1. 与当前仓库结构保持一致，不随意新增顶层目录
  2. 遵循DRY/KISS/YAGNI原则，保持实现最小可用与可维护
  3. 类型优先，虽然项目是Vue而非TypeScript，但仍需注重类型安全
- 影响面：代码规范、目录结构、组件开发、状态管理等

## 变更清单（按文件分组）
- `ai-docs/2025-10-23__frontend__dev-spec.md`
  - 变更点：创建前端开发规范文档
  - 片段/伪代码/要点：
    ```md
    # 前端开发规范
    
    ## 1. 总体原则
    - 与当前仓库结构保持一致
    - DRY/KISS/YAGNI原则
    - 类型优先
    - 可测试性
    - 可观察性
    - 安全与健壮性
    
    ## 2. 技术栈与工具链
    - 框架：Vue 3 + Vue Router + Pinia
    - UI：Naive UI组件库
    - 网络：Axios
    - 构建：Vue CLI
    - 包管理：npm
    
    ## 3. 目录结构与放置约定
    frontend/
    ├─ public/                 # 公共静态资源
    ├─ src/
    │  ├─ api/                 # API接口封装
    │  ├─ components/          # 可复用通用组件
    │  ├─ composables/         # 可复用逻辑（Vue Composition API）
    │  ├─ constants/           # 常量定义
    │  ├─ router/              # 路由配置
    │  ├─ stores/              # 状态管理
    │  ├─ styles/              # 全局样式
    │  ├─ utils/               # 工具函数
    │  ├─ views/               # 页面级组件
    │  ├─ App.vue              # 根组件
    │  └─ main.js              # 入口文件
    
    ## 4. 代码风格与静态检查
    - ES6+语法规范
    - 使用ESLint和Prettier统一代码风格
    - 组件命名：大驼峰命名法（PascalCase）
    - 文件命名：短横线命名法（kebab-case）
    - 变量/函数命名：小驼峰命名法（camelCase）
    - 常量命名：大写下划线命名法（UPPER_SNAKE_CASE）
    
    ## 5. 路由与页面
    - 路由分层：在src/router/按功能模块拆分
    - 页面级组件：放在src/views/目录下
    - 路由懒加载：使用动态import实现代码分割
    
    ## 6. 服务与API访问
    - axios实例：在src/api/index.js创建唯一实例
    - 模块化API：按业务领域组织API（如userAPI、sessionAPI等）
    - 错误处理：统一错误拦截和处理
    
    ## 7. 状态管理（Pinia）
    - Store位置：src/stores/，每个业务一个文件
    - 持久化：仅在必要时使用持久化插件
    - 命名规范：使用useXxxStore格式命名
    
    ## 8. 可复用逻辑（Composables）
    - Composables位置：src/composables/，按功能划分
    - 命名规范：使用useXxx格式命名，如useScrollManager
    - 功能单一：每个composable应关注单一功能点
    
    ## 9. 组件与样式
    - 组件分类：通用组件(src/components/)与页面组件(src/views/)
    - 文件组织：一个组件一个文件，复杂组件可单独目录
    - 样式选择：使用Naive UI组件库为主，局部定制样式
    - 受控组件：优先使用受控写法
    
    ## 9. 表单与校验
    - 使用Naive UI表单组件
    - 所有必填项必须声明规则与错误提示
    - 输入校验：所有表单与URL参数均需校验与转义
    
    ## 10. 实时通信（WebSocket）
    - WebSocket连接：在组件中创建并在store中存储引用
    - 事件监听：通过全局事件进行组件间通信
    - 资源清理：在组件卸载时关闭连接并移除事件监听器
    
    ## 10. 国际化与多语言
    - 如需国际化，在组件旁创建i18n目录
    - Key命名：featureName.action.desc格式
    - 不得在代码中硬编码文案，统一走i18n
    
    ## 11. 测试与质量门禁
    - 单元测试：使用Vitest或项目已有的测试框架
    - 组件测试：使用Vue Test Utils
    - 覆盖率：新增代码行覆盖率≥80%
    - PR必须通过lint/type-check/test/build
    
    ## 12. 性能与体验
    - 代码分割：路由级懒加载+按需导入
    - 列表优化：大数据量使用分页
    - 并发与取消：组件卸载时取消未完成请求
    - 图片与静态资源：放置在public/并开启压缩与缓存配置
    
    ## 13. 安全规范
    - 输入校验：所有表单与URL参数均需校验与转义
    - 认证信息：Token仅通过Header传递
    - 敏感信息：严禁在代码中硬编码密钥、内网地址等
    - 依赖升级：遵循npm audit与CI安全扫描结果进行修复
    
    ## 14. 提交与版本
    - Commit：遵循Conventional Commits（feat:、fix:、refactor:、docs:、test:、chore:）
    - PR规范：说明背景、变更点、风险点、验证方式与截图/GIF
    - 变更日志：自动生成或在发布脚本中聚合
    
    ## 15. 代码生成
    当创建某功能页/模块时，统一生成以下骨架：
    - 页面FeatureX
      - src/views/FeatureX.vue（页面组件）
      - src/api/index.js（在现有API对象中添加新模块条目）
      - src/stores/featureX.js（独立的Pinia Store）
      - src/components/FeatureX/（若有通用子组件则抽到此处）
      - src/composables/useFeatureX.js（若有可复用逻辑则抽到此处）
      - src/router/index.js（在现有路由配置中添加新路由）
      - src/views/FeatureX/__tests__/（基础测试）
    
    ## 16. 审查清单（自检）
    - [ ] 目录位置正确（未越层、未新增顶层目录）
    - [ ] 代码通过lint检查
    - [ ] 路由懒加载、API模块化、状态管理与页面解耦
    - [ ] 表单校验、错误兜底、空态与加载态齐全
    - [ ] 组件可复用、粒度合理、无重复代码
    - [ ] 单元测试覆盖关键路径
    - [ ] 静态资源按规定位置存放
    - [ ] WebSocket连接正确管理（创建、使用、清理）
    ```

## 指令与运行
```bash
# 开发
npm run serve

# 构建
npm run build

# 代码检查
npm run lint
```