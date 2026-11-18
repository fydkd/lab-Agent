# 智能实验室预约系统（lab-agent）

基于 **Vue 3 + FastAPI + LangGraph** 的前后端分离 Web 应用，面向学生的实验室与设备预约管理场景。系统支持学生在线浏览实验室与设备、提交预约、查看预约进度，管理员管理实验室、设备、用户并审核预约，同时内置 **AI 智能助手**：基于大模型 Function Calling 与 RAG 知识库检索，支持自然语言查询实验室信息、预约规则，并可通过对话直接完成真实预约落库。

---

## 一、技术栈

| 层级 | 技术选型 | 版本要求 |
| --- | --- | --- |
| 前端框架 | Vue 3（Composition API，`<script setup>`） | vue ^3.5.42 |
| 构建工具 | Vite | ^8.2.2 |
| 路由 | Vue Router（History 模式） | ^5.3.1 |
| UI 组件库 | Element Plus + @element-plus/icons-vue | ^2.14.7 |
| HTTP 请求 | axios（流式对话使用原生 fetch） | ^1.20.0 |
| Markdown 渲染 | marked + DOMPurify（XSS 防护） | ^18.1.1 / ^3.4.17 |
| 运行环境 | Node.js | ^22.18.0 或 >=24.12.0 |
| 后端框架 | FastAPI | 0.115.13 |
| ASGI 服务器 | Uvicorn | 0.34.0 |
| ORM | SQLAlchemy（2.0 风格 Mapped 注解） | 2.0.41 |
| 数据校验 | Pydantic v2 / pydantic-settings | pydantic-settings 2.7.1 |
| 数据库 | MySQL（PyMySQL 驱动） | pymysql 1.1.1 |
| 密码加密 | bcrypt | 5.0.0 |
| 登录认证 | PyJWT（JWT 令牌） | 2.13.0 |
| Agent 框架 | LangGraph + langchain-openai | langgraph 1.2.15 |
| 向量检索 | ChromaDB + sentence-transformers（BAAI/bge-small-zh-v1.5） | chromadb 1.5.9 |
| Python | CPython | 3.12 |

## 二、功能概览

| 角色 | 功能 |
| --- | --- |
| 学生 | 注册 / 登录、首页数据概览、浏览实验室与设备、提交实验室 / 设备预约、查看与取消自己的预约、AI 智能助手对话与预约、个人信息维护、修改密码 |
| 管理员 | 登录、首页数据概览、实验室管理（增删改查）、设备管理（增删改查）、预约审核（通过 / 拒绝）、用户管理（增删改查）、AI 智能助手 |

核心能力：

- **登录认证**：JWT 令牌 + bcrypt 密码哈希，前端路由守卫 + 后端鉴权依赖双重控制。
- **角色权限**：区分 student / admin，后端 `get_current_admin` 依赖拦截非管理员请求，前端按角色渲染菜单。
- **预约全流程**：时间合法性校验（不可预约过去时段、不可超出实验室开放时段）、时段冲突检测、管理员审核、学生取消、后台任务每分钟自动将过期的待审核预约置为已取消。
- **AI 智能助手**：LangGraph ReAct Agent，挂载 5 个工具（知识库检索、开放实验室查询、实验室设备查询、创建预约、当前日期查询），SSE 流式输出，前端实时展示 token 流与工具调用过程；创建预约前强制用户确认，并通过实验室名称与 lab_id 交叉校验防止误预约。
- **RAG 知识库**：实验室规则、安全规范等 Markdown 文档经 bge-small-zh-v1.5 嵌入后存入 ChromaDB，检索结果按相关度阈值过滤后注入大模型上下文。
- **文件上传**：头像、实验室封面、设备图片上传（扩展名白名单 + 100MB 大小限制），上传后通过 `/uploads/` 静态路径访问。

## 三、目录结构

```
lab-agent/
├── backend/                    # 后端工程（FastAPI）
│   ├── .env                    # 环境变量（数据库连接串、JWT 配置、LLM 配置）
│   ├── requirements.txt        # Python 依赖清单
│   ├── uploads/                # 上传文件存储目录（挂载为 /uploads 静态路径）
│   ├── data/
│   │   ├── kb/                 # 知识库 Markdown 源文件（预约规则、安全规范等）
│   │   └── chroma/             # ChromaDB 向量索引（自动生成）
│   └── app/
│       ├── main.py             # 应用入口：FastAPI 实例、路由注册、自动建表、CORS、静态目录、生命周期任务
│       ├── config.py           # 配置读取（pydantic-settings）、上传目录与文件限制
│       ├── database.py         # 数据库引擎、会话工厂、Base 基类
│       ├── api/                # 路由层（__init__.py 聚合路由，统一 /api 前缀）
│       │   ├── auth.py         # 认证：登录、注册
│       │   ├── user.py         # 用户：个人信息、修改密码、管理员用户管理
│       │   ├── files.py        # 文件上传
│       │   ├── lab.py          # 实验室：列表 / 详情（登录）、增删改（管理员）
│       │   ├── equipment.py    # 设备：列表（登录）、增删改（管理员）
│       │   ├── reservation.py  # 预约：列表、创建、审核、取消
│       │   └── ai.py           # AI 对话：SSE 流式接口
│       ├── common/             # 统一响应封装（Response / PageResponse）与全局异常处理
│       ├── dependencies/       # get_current_user / get_current_admin 鉴权依赖
│       ├── models/             # SQLAlchemy 模型：users / labs / equipments / reservations
│       ├── schemas/            # Pydantic 请求 / 响应模型
│       ├── services/           # 业务逻辑层
│       │   ├── agent_service.py   # LangGraph Agent 构建与流式事件输出
│       │   ├── agent_tools.py     # Agent 工具集（知识库检索、实验室/设备查询、创建预约等）
│       │   ├── kb_service.py      # ChromaDB 向量知识库（嵌入、检索、预热）
│       │   ├── reservation_service.py # 预约校验、冲突检测、过期扫描任务
│       │   └── ...                # auth / user / lab / equipment 等业务服务
│       └── utils/              # bcrypt 密码哈希、JWT 生成 / 解析
└── frontend/                   # 前端工程（Vue 3 + Vite）
    ├── index.html              # HTML 入口
    ├── vite.config.js          # Vite 配置（@ 路径别名等）
    ├── package.json
    └── src/
        ├── main.js             # 应用入口
        ├── App.vue             # 根组件
        ├── api/                # 接口请求层（auth / user / lab / equipment / reservation / ai / file）
        ├── router/index.js     # 路由表（含登录态路由守卫）
        ├── layouts/Layout.vue  # 后台整体布局（顶栏 + 按角色渲染的侧边菜单）
        ├── components/         # 可复用组件（ReserveDialog 预约对话框）
        ├── views/              # 页面组件（登录、注册、首页、AI 助手、实验室、设备、预约、审核、用户、个人信息、修改密码）
        ├── utils/              # axios 实例、本地存储、useUser composable
        └── assets/             # 全局样式与系统 Logo
```

## 四、系统架构

```
┌──────────────────────────┐        HTTP / JSON        ┌──────────────────────────┐
│       前端（Browser）      │  ───────────────────────▶ │      后端（FastAPI）       │
│  Vue 3 + Vue Router      │   REST API + SSE 流式对话   │  Uvicorn (ASGI)          │
│  Element Plus            │ ◀───────────────────────  │  RESTful API             │
└──────────────────────────┘                            └──────┬───────────┬───────┘
                                                               │           │
                                              SQLAlchemy ORM   │           │ LangGraph Agent
                                                               ▼           ▼
                                                   ┌─────────────────┐  ┌────────────────────┐
                                                   │      MySQL       │  │   ChromaDB 向量库    │
                                                   │ 数据库：lab-agent │  │（知识库 RAG 检索）   │
                                                   └─────────────────┘  └─────────┬──────────┘
                                                                                   │
                                                                                   ▼
                                                                        ┌────────────────────┐
                                                                        │  大模型（OpenAI 兼容） │
                                                                        │ Function Calling    │
                                                                        └────────────────────┘
```

- 前端使用 History 模式路由，页面分为「登录 / 注册」独立页与「/manager 后台布局」两部分，侧边菜单按用户角色动态渲染。
- 后端按 `api（路由）→ services（业务逻辑）→ models（ORM）` 分层，统一响应封装与全局异常处理，业务路由聚合在 `/api` 前缀下，配置通过 `.env` 注入。
- 服务启动时由 SQLAlchemy `Base.metadata.create_all` 自动创建数据表（数据库需提前创建）；生命周期内完成向量库预热，并启动预约过期扫描后台任务（每分钟执行一次）。
- AI 对话链路：前端 fetch 发起 SSE 请求 → 后端 LangGraph Agent 流式执行 → 大模型决策调用工具（查知识库 / 查实验室 / 查设备 / 创建预约）→ 事件流实时推送到前端渲染。

## 五、快速开始

### 5.1 启动后端

前置条件：已安装 Python 3.12、本机 MySQL 服务可用。

```bash
# 1. 进入后端目录
cd backend

# 2. 创建并激活虚拟环境（Windows PowerShell）
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. 安装依赖
pip install -r requirements.txt

# 4. 在 MySQL 中创建数据库
#    CREATE DATABASE `lab-agent` DEFAULT CHARACTER SET utf8mb4;

# 5. 确认 / 修改 .env 中的配置
#    DATABASE_URL=mysql+pymysql://root:123456@127.0.0.1:3306/lab-agent
#    JWT_SECRET_KEY=<随机字符串>   JWT_EXPIRE_HOURS=24   JWT_ALGORITHM=HS256
#    LLM_API_KEY=<大模型密钥>      LLM_MODEL=<模型名>    LLM_BASE_URL=<OpenAI 兼容接口地址>

# 6. 启动服务（在 backend 目录下执行）
uvicorn app.main:app --reload
```

> 说明：首次启动会下载 BAAI/bge-small-zh-v1.5 嵌入模型并缓存到本地；代码已设置 `HF_HUB_OFFLINE=1` / `TRANSFORMERS_OFFLINE=1`，模型缓存完成后可离线运行。知识库源文件位于 `backend/data/kb/*.md`，首次启动自动构建向量索引到 `backend/data/chroma/`。

启动后访问：

- 根路径健康检查：http://127.0.0.1:8000/
- 交互式接口文档（Swagger UI）：http://127.0.0.1:8000/docs
- 备用文档（ReDoc）：http://127.0.0.1:8000/redoc

### 5.2 启动前端

前置条件：Node.js 版本满足 `^22.18.0 或 >=24.12.0`。

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器（默认 http://localhost:5173）
npm run dev
```

其他命令：

```bash
npm run build     # 生产环境打包，产物输出到 dist/
npm run preview   # 本地预览生产构建产物
npm run format    # 使用 Prettier 格式化 src/ 目录
```

## 六、数据模型概览

系统共四张核心表（均含公共字段 id / create_time / update_time）：

### users（用户信息）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| username | varchar(50) | 登录账号，非空 |
| password | varchar(255) | 密码（**bcrypt 哈希串存储**） |
| name | varchar(50) | 用户名称 |
| role | varchar(50) | 角色：`student`-学生，`admin`-管理员 |
| email / phone / avatar | varchar(50) | 邮箱 / 手机号 / 头像地址，可空 |
| status | int | 状态：0-禁用，1-正常 |

### labs（实验室信息）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| name | varchar(50) | 名称 |
| description | varchar(255) | 简介 |
| img | varchar(100) | 封面 |
| location | varchar(100) | 位置 |
| capacity | int | 容量 |
| open_time / close_time | varchar(20) | 开放 / 关闭时间 |
| status | int | 状态：0-关闭，1-开放 |

### equipments（实验室设备）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| lab_id | int（外键 → labs.id） | 所属实验室 |
| name | varchar(50) | 设备名称 |
| description | varchar(500) | 设备描述 |
| img | varchar(255) | 设备图片 |
| spec | varchar(100) | 设备规格 |
| quantity | int | 设备数量 |
| status | int | 状态：0-维修，1-正常 |

### reservations（预约信息）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| user_id | int（外键 → users.id） | 预约用户 |
| lab_id | int（外键 → labs.id） | 预约实验室 |
| equipment_id | int（外键 → equipments.id） | 预约设备，可空（为空表示整间实验室预约） |
| date | varchar(20) | 预约日期（YYYY-MM-DD） |
| start_time / end_time | varchar(20) | 开始 / 结束时间（HH:MM） |
| remark | varchar(255) | 备注 |
| status | int | 状态：0-待审核，1-已通过，2-已拒绝，3-已取消 |

## 七、相关文档

- [前端说明文档](./frontend/README.md)
- [后端说明文档](./backend/README.md)
