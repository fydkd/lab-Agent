# 后端说明文档 —— 智能实验室预约系统

智能实验室预约系统的后端工程，基于 **FastAPI + SQLAlchemy 2.0 + MySQL** 构建，为前端提供 RESTful API 与数据持久化服务。认证体系采用 **JWT + bcrypt 密码哈希**，并区分学生 / 管理员两类角色的接口权限。AI 能力基于 **LangGraph ReAct Agent + ChromaDB 向量知识库**，支持自然语言查询实验室信息、检索预约规则文档，以及通过对话完成真实预约落库，对话内容以 SSE 流式推送到前端。

---

## 一、技术栈与依赖

依赖清单见 [requirements.txt](requirements.txt)：

| 依赖 | 版本 | 用途 |
| --- | --- | --- |
| fastapi | 0.115.13 | Web 框架，自动生成 OpenAPI / Swagger 文档 |
| uvicorn | 0.34.0 | ASGI 服务器，用于运行 FastAPI 应用 |
| sqlalchemy | 2.0.41 | ORM 框架，使用 2.0 新式 `Mapped` / `mapped_column` 注解 |
| pymysql | 1.1.1 | 纯 Python 的 MySQL 驱动（连接串协议名 `mysql+pymysql`） |
| pydantic-settings | 2.7.1 | 基于 Pydantic v2 的环境变量 / 配置文件管理 |
| bcrypt | 5.0.0 | 密码哈希加密与校验 |
| PyJWT | 2.13.0 | JWT 登录令牌的生成与解析 |
| python-multipart | 0.0.32 | 文件上传（multipart/form-data）解析 |
| openai | 3.29.0 | OpenAI 兼容接口客户端 |
| langgraph | 1.2.15 | Agent 工作流编排（ReAct 图结构） |
| langchain-openai | 1.7.2 | LangChain 的 OpenAI 兼容模型封装（ChatOpenAI） |
| langchain-core | 1.6.11 | LangChain 核心抽象（消息、工具等） |
| chromadb | 1.5.9 | 本地持久化向量数据库（知识库检索） |
| sentence-transformers | 6.1.0 | 中文嵌入模型 BAAI/bge-small-zh-v1.5 加载与向量化 |

运行环境：**Python 3.12**（虚拟环境位于 `backend/.venv`）。

## 二、目录结构

```
backend/
├── .env                      # 环境变量文件（数据库连接串、JWT 配置、LLM 配置）
├── requirements.txt          # Python 依赖清单
├── uploads/                  # 上传文件存储目录（挂载为 /uploads 静态路径）
├── data/
│   ├── kb/                   # 知识库 Markdown 源文件（预约规则、安全规范、开放时间、设备使用）
│   └── chroma/               # ChromaDB 向量索引（自动生成，无需入库）
└── app/                      # 应用主包
    ├── __init__.py
    ├── main.py               # 应用入口：FastAPI 实例、路由注册、自动建表、CORS、静态目录、生命周期任务
    ├── config.py             # 配置类 Settings，读取 .env；上传目录与文件限制
    ├── database.py           # 引擎、会话工厂、依赖注入、Base 声明基类
    ├── api/                  # 路由层（按业务模块组织）
    │   ├── __init__.py       # 路由聚合：APIRouter(prefix="/api")，挂载各业务子路由
    │   ├── auth.py           # 认证接口：登录、注册
    │   ├── user.py           # 用户信息接口：个人信息、修改密码、管理员用户管理
    │   ├── files.py          # 文件上传接口
    │   ├── lab.py            # 实验室接口：列表 / 详情（登录）、增删改（管理员）
    │   ├── equipment.py      # 设备接口：列表（登录）、增删改（管理员）
    │   ├── reservation.py    # 预约接口：分页列表、创建、审核（管理员）、取消
    │   └── ai.py             # AI 对话接口：POST /ai/chat/stream（SSE 流式）
    ├── common/               # 公共层：统一响应封装与全局异常处理
    │   ├── response.py       # Response 统一响应模型、PageResponse 分页模型
    │   └── exceptions.py     # BusinessException 业务异常与四类异常处理器
    ├── dependencies/         # 通用依赖注入层
    │   └── auth.py           # get_current_user 登录鉴权、get_current_admin 管理员鉴权
    ├── models/               # 数据模型层（SQLAlchemy ORM）
    │   ├── user.py           # User 用户模型（users）
    │   ├── lab.py            # Lab 实验室模型（labs）
    │   ├── equipment.py      # Equipment 设备模型（equipments，外键关联 labs）
    │   └── reservation.py    # Reservation 预约模型（reservations，外键关联 users / labs / equipments）
    ├── schemas/              # 数据校验层（Pydantic 模型）
    │   ├── auth.py           # LoginRequest / LoginResponse / RegisterRequest
    │   ├── user.py           # UserResponse / UserCreateRequest / UserUpdateRequest / PasswordUpdateRequest
    │   ├── lab.py            # LabResponse / LabCreateRequest / LabUpdateRequest
    │   ├── equipment.py      # EquipmentResponse / EquipmentCreateRequest / EquipmentUpdateRequest
    │   ├── reservation.py    # ReservationCreateRequest / ReservationResponse / ReservationAuditRequest
    │   ├── ai.py             # ChatMessage / ChatRequest
    │   └── file.py           # FileResponse
    ├── services/             # 业务逻辑层
    │   ├── auth_service.py        # 登录、注册
    │   ├── user_service.py        # 个人信息维护、修改密码、用户分页与增删改
    │   ├── lab_service.py         # 实验室分页查询、详情、增删改
    │   ├── equipment_service.py   # 设备分页查询、增删改
    │   ├── reservation_service.py # 预约创建校验、冲突检测、审核、取消、过期扫描任务
    │   ├── agent_service.py       # LangGraph Agent 构建与流式事件输出
    │   ├── agent_tools.py         # Agent 工具集（5 个工具的构建与执行）
    │   ├── kb_service.py          # ChromaDB 向量知识库（嵌入、检索、启动预热）
    │   └── ai_service.py          # 早期非流式对话实现（已停用，保留参考）
    └── utils/                # 工具层
        ├── password.py       # bcrypt 密码哈希 / 校验
        └── jwt.py            # PyJWT 令牌生成 / 解析
```

分层职责：

```
HTTP 请求（Authorization: Bearer <token>）
   │
   ▼
app/api/           路由层：接收请求、参数校验、调用服务层、返回响应
   │
   ├── app/common/        公共层：统一 Response / PageResponse 响应封装、全局异常处理器
   ├── app/dependencies/  依赖层：登录鉴权（get_current_user）、管理员鉴权（get_current_admin）
   ├── app/schemas/       校验层：Pydantic 模型，定义请求体与响应体结构
   └── app/utils/         工具层：密码哈希、JWT 生成与解析
   │
   ▼
app/services/      服务层：业务逻辑、Agent 工作流、向量检索、后台任务
   │
   ▼
app/models/        模型层：SQLAlchemy ORM，映射数据库表
   │
   ▼
app/database.py    数据库连接：engine 引擎 + SessionLocal 会话
```

## 三、环境准备与启动

### 3.1 准备数据库

确保本机 MySQL 服务已启动，并创建数据库（表由应用自动创建，无需手动建表）：

```sql
CREATE DATABASE `lab-agent` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

### 3.2 配置环境变量

[.env](.env) 配置项：

```ini
# 数据库链接
DATABASE_URL=mysql+pymysql://root:123456@127.0.0.1:3306/lab-agent
# JWT相关配置
JWT_SECRET_KEY=OB9PHpiNMkazI2NXNNLfIA5zKQ151ZDxHYjzeLHf4lb
JWT_EXPIRE_HOURS=24
JWT_ALGORITHM=HS256
# LLM相关配置（OpenAI 兼容接口）
LLM_API_KEY=<大模型API密钥>
LLM_MODEL=<模型名称>
LLM_BASE_URL=<接口基础地址>
```

数据库连接串格式：

```
mysql+pymysql://用户名:密码@主机:端口/数据库名
```

配置由 [app/config.py](app/config.py) 中的 `Settings` 类在启动时自动加载（UTF-8 编码）。

> 安全提示：`.env` 包含明文数据库密码、JWT 密钥与 LLM 密钥，已被仓库根目录 [.gitignore](../.gitignore) 忽略，不要提交到版本库；生产环境的 `JWT_SECRET_KEY` 应替换为独立的随机字符串。

### 3.3 安装依赖并启动

所有命令均在 `backend/` 目录下执行：

```bash
# 1. 创建虚拟环境
python -m venv .venv

# 2. 激活虚拟环境
# Windows PowerShell：
.\.venv\Scripts\Activate.ps1
# Windows CMD：
.\.venv\Scripts\activate.bat
# Linux / macOS：
# source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动开发服务（--reload 开启代码热重载）
uvicorn app.main:app --reload
```

启动成功后默认监听 http://127.0.0.1:8000 ，可访问：

| 地址 | 说明 |
| --- | --- |
| http://127.0.0.1:8000/ | 根路径健康检查，返回 `{"message": "FastAPI工程正在运行中"}` |
| http://127.0.0.1:8000/docs | Swagger UI 交互式接口文档（可在线调试，右上角 Authorize 可填 Token） |
| http://127.0.0.1:8000/redoc | ReDoc 风格接口文档 |
| http://127.0.0.1:8000/uploads/xxx | 上传文件的静态访问路径 |

> 首次启动说明：向量库模块会下载 BAAI/bge-small-zh-v1.5 嵌入模型并缓存到本地；[kb_service.py](app/services/kb_service.py) 已设置 `HF_HUB_OFFLINE=1` / `TRANSFORMERS_OFFLINE=1`，模型缓存完成后不再发起网络检查，可离线启动。

## 四、核心模块说明

### 4.1 [app/main.py](app/main.py) —— 应用入口

- 模块加载时执行 `Base.metadata.create_all(bind=engine)`：依据所有继承自 `Base` 的模型自动创建数据表（已存在的表不会被修改或重建）。
- 通过 `lifespan` 异步上下文管理应用生命周期：
  - 启动时调用 `kb_service.warmup()` 预热向量库（初始化嵌入模型、加载或构建索引）；
  - 启动 `reservation_service.run_expire_scan()` 后台任务，每分钟扫描一次，将已过期的待审核预约自动置为「已取消」；
  - 关闭时取消后台任务并等待其退出。
- 通过 `add_middleware(CORSMiddleware, ...)` 配置跨域：`allow_origins` 为 `http://localhost:5173` 与 `http://127.0.0.1:5173`，`allow_credentials=True`，允许前端携带 `Authorization` 请求头访问。
- 通过 `app.mount("/uploads", StaticFiles(...))` 将上传目录挂载为静态路径。
- 注册四类异常处理器（业务异常 → HTTP 异常 → 参数校验异常 → 全局兜底，兜底最后注册），统一接口错误返回结构。
- 保留根路由 `GET /` 作为健康检查。

### 4.2 [app/config.py](app/config.py) —— 配置管理

- 使用 pydantic-settings 的 `BaseSettings`，将配置与代码分离；`BASE_DIR` 指向后端项目根目录，据此定位 `.env`。
- 配置项：

| 配置项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `DATABASE_URL` | str | 无（必填） | 数据库连接串 |
| `JWT_SECRET_KEY` | str | 无（必填） | JWT 签名密钥 |
| `JWT_EXPIRE_HOURS` | int | 24 | Token 有效期（小时） |
| `JWT_ALGORITHM` | str | HS256 | JWT 签名算法 |
| `LLM_API_KEY` | str | 无（必填） | 大模型 API 密钥 |
| `LLM_MODEL` | str | 无（必填） | 大模型名称 |
| `LLM_BASE_URL` | str | 无（必填） | OpenAI 兼容接口基础地址 |

- 导出单例 `settings`，其他模块通过 `from app.config import settings` 使用。
- 同时定义上传相关常量：`UPLOAD_DIR`（启动时自动创建）、`MAX_FILE_SIZE`（100MB）、`ALLOWED_EXTENSIONS`（图片 / 文档 / 压缩包扩展名白名单）。

### 4.3 [app/database.py](app/database.py) —— 数据库连接与基类

- `engine = create_engine(settings.DATABASE_URL)`：创建数据库引擎。
- `SessionLocal = sessionmaker(engine, autoflush=False)`：数据库会话工厂。
- `get_db()`：FastAPI 依赖注入函数，生成会话并在请求结束后保证关闭。
- `Base(DeclarativeBase)`：所有 ORM 模型的声明基类，统一定义三个公共字段：id（主键自增）、create_time（创建时间）、update_time（更新时间，更新时自动刷新）。

### 4.4 [app/models/](app/models/) —— 数据模型

四张业务表均继承 `Base`，自动拥有 id / create_time / update_time：

- **users（用户信息）**：username、password（bcrypt 哈希串）、name、role（student / admin）、email、phone、avatar、status（0-禁用，1-正常）。
- **labs（实验室信息）**：name、description、img、location、capacity、open_time、close_time、status（0-关闭，1-开放）。
- **equipments（实验室设备）**：lab_id（外键 → labs.id）、name、description、img、spec、quantity、status（0-维修，1-正常），通过 `relationship()` 关联所属实验室。
- **reservations（预约信息）**：user_id（外键 → users.id）、lab_id（外键 → labs.id）、equipment_id（外键 → equipments.id，可空，为空表示整间实验室预约）、date、start_time、end_time、remark、status（0-待审核，1-已通过，2-已拒绝，3-已取消），并分别关联 user / lab / equipment 对象。

### 4.5 [app/schemas/](app/schemas/) —— Pydantic 校验模型

- 响应模型（`*Response`）均通过 `model_config = ConfigDict(from_attributes=True)` 支持从 ORM 对象直接转换；`UserResponse` 刻意不包含 password 字段，避免密码随接口外泄。
- 请求模型（`*CreateRequest` / `*UpdateRequest`）定义创建与更新的入参，更新类请求字段全部可空，仅更新传入字段。
- [ai.py](app/schemas/ai.py)：`ChatRequest` 包含 `messages: list[ChatMessage]`，为前端传入的完整对话历史。

### 4.6 [app/common/](app/common/) —— 统一响应与全局异常

- [response.py](app/common/response.py)：
  - `Response`：统一响应模型（`code` / `message` / `data`），`Response.success(...)` 固定 `code=200`，`Response.error(...)` 构造失败响应；
  - `PageResponse`：分页结果模型（`list` / `total`）。
- [exceptions.py](app/common/exceptions.py)：业务异常 `BusinessException(message, code=500)` 与四个处理器，均在 [main.py](app/main.py) 启动时注册：

| 处理器 | 捕获异常 | HTTP 状态码 | 响应体 |
| --- | --- | --- | --- |
| business_exception_handler | `BusinessException` | 200 | `{"code": 异常code(默认500), "message": ..., "data": null}` |
| http_exception_handler | `HTTPException` | 异常的 status_code | `{"code": status_code, "message": detail, "data": null}` |
| validation_exception_handler | `RequestValidationError` | 422 | `{"code": 422, "message": "请求参数错误", "data": null}` |
| global_exception_handler | `Exception`（兜底，最后注册） | 500 | `{"code": 500, "message": "服务器内部错误", "data": null}` |

### 4.7 [app/dependencies/auth.py](app/dependencies/auth.py) —— 鉴权依赖

- `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")`：从请求头 `Authorization: Bearer <token>` 提取令牌，同时驱动 Swagger UI 的 Authorize 按钮。
- `get_current_user`：解析并校验 Token（失效抛 401「登录已失效，请重新登录」），校验 `user_id` 载荷、用户存在性与账号状态，返回 `User` 对象。
- `get_current_admin`：在 `get_current_user` 基础上校验 `role == "admin"`，非管理员抛出 `BusinessException(message="无权限访问", code=403)`。

### 4.8 [app/services/reservation_service.py](app/services/reservation_service.py) —— 预约核心逻辑

- **创建预约（create_reservation）** 依次校验：
  1. 时间合法性：预约日期不早于今天；结束时间不早于开始时间；当天预约的结束时间不早于当前时间；
  2. 实验室存在且状态为开放；预约时段在实验室开放 / 关闭时间范围内；
  3. 指定设备时，设备存在且状态为正常（非维修）；
  4. 时段冲突检测：同一实验室（含同设备维度）在相同日期、状态为待审核 / 已通过的记录中，存在时间区间重叠则拒绝（「实验室该时段已被预约」）；
  5. 校验通过后落库，初始状态为 `0-待审核`。
- **取消预约（cancel_reservation）**：仅本人可取消，且仅「待审核」状态可取消，置为 `3-已取消`。
- **审核预约（audit_reservation）**：仅管理员，仅「待审核」状态可审核，置为 `1-已通过` 或 `2-已拒绝`。
- **过期扫描（run_expire_scan）**：应用启动后常驻的异步后台任务，每分钟执行一次 `expire_pending_reservations`，将预约日期已过、或当天但结束时间已过的待审核预约批量置为「已取消」。
- **分页列表（get_reservation_page_list）**：学生仅返回本人记录，管理员返回全部记录；响应中补充 user_name / lab_name / equipment_name 与 type（设备 / 实验室）。

### 4.9 [app/services/agent_service.py](app/services/agent_service.py) + [agent_tools.py](app/services/agent_tools.py) —— AI Agent

**Agent 构建（build_agent）**：

- 使用 `ChatOpenAI`（读取 `.env` 的 LLM 配置，`temperature=0`，开启 streaming），通过 `bind_tools` 绑定工具集；
- 基于 LangGraph 的 `StateGraph(MessagesState)` 构建 ReAct 图：`START → agent（调用大模型）→（有 tool call 则进入 tools 节点执行，结果回传 agent；无则结束）`，递归上限 10 轮。

**系统提示词（SYSTEM_PROMPT）** 要点：

- 声明可用工具与用途；系统提示末尾动态注入当前真实日期与星期，要求所有「今天 / 明天 / 下周」等日期换算以此为基准；
- **lab_id 准确性约束**：lab_id 必须从 `list_open_labs` 返回结果中逐字复制，禁止猜测；调用 `create_lab_reservation` 必须同时传入 `lab_name` 用于工具内部交叉校验，名称不匹配时必须重新查询而不是重试错误 id；
- **预约确认流程**：提交预约前必须向用户复述实验室（或设备）ID 与名称、日期、起止时间，并获得用户明确确认后才允许调用创建工具；
- 预约成功后状态为待审核，需管理员审核通过；规则类问题优先走 `search_lab_docs` 知识库检索，禁止编造数据库中不存在的信息。

**工具集（build_tools，按请求绑定当前用户与数据库会话）**：

| 工具 | 说明 |
| --- | --- |
| `search_lab_docs(query)` | 在 ChromaDB 知识库中检索实验室规则文档，返回相关片段 |
| `list_open_labs(keywords)` | 分页查询状态为开放的实验室（id、名称、位置、容量、开放时段） |
| `list_lab_equipment(lab_id, keywords)` | 查询指定实验室下的设备列表（含设备状态） |
| `create_lab_reservation(lab_id, date, start_time, end_time, lab_name, equipment_id?, remark?)` | 创建真实预约落库；先用 lab_id 查询真实实验室名称与传入 lab_name 交叉校验，不匹配直接返回错误并要求重新查询；落库复用 `reservation_service.create_reservation` 的全部业务校验 |
| `get_today()` | 返回当前日期（备用校验） |

**流式输出（stream_agent）**：通过 `agent.astream_events(version="v2")` 将执行过程转为事件流，向前端推送四类事件：

- `status`：状态提示（如「正在思考中，请稍后...」）；
- `tool_start` / `tool_end`：工具调用开始 / 结束，附带工具中文标签与输出预览（截取前 200 字符）；
- `token`：大模型增量输出的文本片段（仅 agent 节点）；
- `done` / `error`：结束 / 异常（业务异常返回具体 message，其他异常统一提示「大模型调用失败，请稍后重试」）。

### 4.10 [app/services/kb_service.py](app/services/kb_service.py) —— 向量知识库

- 使用 ChromaDB `PersistentClient` 持久化到 `backend/data/chroma/`，集合名 `lab_kb`；
- 嵌入模型为 BAAI/bge-small-zh-v1.5（sentence-transformers），模块加载时设置 `HF_HUB_OFFLINE=1` / `TRANSFORMERS_OFFLINE=1`，模型缓存后离线运行；
- 首次初始化（集合为空）时，读取 `backend/data/kb/` 下全部 `.md` 文件（预约规则、安全规范、开放时间、设备使用），以文件名作为 id 与 metadata.source 批量写入向量库；
- `warmup()` 在应用启动时执行一次查询，提前完成模型加载与索引初始化；
- `search(query)`：全量检索后按 `score = 1 / (1 + distance)` 计算相关度，过滤 score < 0.5 的结果，按相关度降序取前 2 篇，拼接为 `[文件名]\n内容` 格式的上下文返回；无结果时返回空串。

### 4.11 [app/api/files.py](app/api/files.py) —— 文件上传

`POST /api/files/upload`：接收 multipart 文件，校验文件名非空、扩展名在白名单内、大小不超过 100MB；落盘文件名采用「毫秒时间戳_UUID 前 8 位」保证唯一，保存到 `uploads/` 目录，返回原始文件名、落盘文件名、大小与访问 URL（`/uploads/<disk_name>`）。

### 4.12 [app/utils/](app/utils/) —— 工具层

- [password.py](app/utils/password.py)：`hash_password` 生成随机盐 bcrypt 哈希；`verify_password` 校验明文与哈希。
- [jwt.py](app/utils/jwt.py)：`create_access_token(user_id)` 签发载荷为 `{"user_id": ..., "exp": ...}` 的 JWT；`decode_access_token` 解析并校验签名与有效期，失败抛异常（由鉴权依赖统一转为 401）。

## 五、接口一览

统一约定：

- 除健康检查外，所有业务接口前缀为 `/api`，响应均为统一结构 `{"code", "message", "data"}`；
- 需登录的接口要求请求头 `Authorization: Bearer <token>`；
- 标注「管理员」的接口由 `get_current_admin` 保护，非管理员返回 `code=403`。

### 5.1 健康检查

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 返回 `{"message": "FastAPI工程正在运行中"}` |

### 5.2 认证（/api/auth）

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| POST | `/api/auth/login` | 登录，返回 token 与用户信息 | 无 |
| POST | `/api/auth/register` | 注册（默认角色 student） | 无 |

### 5.3 用户（/api/user）

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| GET | `/api/user/me` | 获取当前登录用户信息 | 登录 |
| PUT | `/api/user/me` | 更新当前用户个人信息（名称 / 邮箱 / 手机号 / 头像） | 登录 |
| PUT | `/api/user/password` | 修改当前用户密码（校验旧密码） | 登录 |
| GET | `/api/user/list` | 用户分页列表（page / page_size / keywords） | 管理员 |
| POST | `/api/user` | 新增用户（默认密码 123，默认角色 student） | 管理员 |
| PUT | `/api/user/{user_id}` | 更新指定用户 | 管理员 |
| DELETE | `/api/user/{user_id}` | 删除指定用户（不可删除自己） | 管理员 |

### 5.4 文件（/api/files）

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| POST | `/api/files/upload` | 上传文件，返回访问 URL | 无 |

### 5.5 实验室（/api/lab）

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| GET | `/api/lab/list` | 实验室分页列表（page / page_size / keywords / status） | 登录 |
| GET | `/api/lab/{lab_id}` | 实验室详情 | 登录 |
| POST | `/api/lab` | 新增实验室 | 管理员 |
| PUT | `/api/lab/{lab_id}` | 更新实验室 | 管理员 |
| DELETE | `/api/lab/{lab_id}` | 删除实验室 | 管理员 |

### 5.6 设备（/api/equipment）

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| GET | `/api/equipment/list` | 设备分页列表（page / page_size / keywords / lab_id） | 登录 |
| POST | `/api/equipment` | 新增设备 | 管理员 |
| PUT | `/api/equipment/{equipment_id}` | 更新设备 | 管理员 |
| DELETE | `/api/equipment/{equipment_id}` | 删除设备 | 管理员 |

### 5.7 预约（/api/reservation）

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| GET | `/api/reservation/list` | 预约分页列表（学生仅本人，管理员全部；支持 status 过滤） | 登录 |
| POST | `/api/reservation` | 创建预约（初始状态：待审核） | 登录 |
| PUT | `/api/reservation/{reservation_id}/audit` | 审核预约（status：1-通过，2-拒绝） | 管理员 |
| PUT | `/api/reservation/{reservation_id}/cancel` | 取消预约（仅本人、仅待审核状态） | 登录 |

### 5.8 AI 对话（/api/ai）

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| POST | `/api/ai/chat/stream` | AI 对话（SSE 流式，`Content-Type: text/event-stream`） | 登录 |

请求体：`{"messages": [{"role": "user"|"assistant", "content": "..."}]}`。

响应为 SSE 事件流，每行格式 `data: {json}\n\n`，事件类型包括：

```json
{"type": "status", "message": "正在思考中，请稍后..."}
{"type": "tool_start", "name": "list_open_labs", "label": "查询开放实验室"}
{"type": "tool_end", "name": "list_open_labs", "label": "查询开放实验室", "preview": "..."}
{"type": "token", "content": "文本片段"}
{"type": "done"}
{"type": "error", "message": "错误信息"}
```
