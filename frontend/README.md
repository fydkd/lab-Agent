# 前端说明文档 —— 智能实验室预约系统

智能实验室预约系统的前端工程，基于 **Vue 3 + Vite + Element Plus** 构建，承担登录注册、后台布局、实验室与设备浏览预约、预约审核、用户管理、个人信息维护，以及 **AI 智能助手**（SSE 流式对话 + Markdown 渲染 + 工具调用过程可视化）的页面展示与交互。

---

## 一、技术栈与依赖

### 运行依赖（dependencies）

| 依赖 | 版本 | 用途 |
| --- | --- | --- |
| vue | ^3.5.42 | 前端框架，全部组件使用 Composition API + `<script setup>` |
| vue-router | ^5.3.1 | 单页应用路由，采用 HTML5 History 模式 |
| element-plus | ^2.14.7 | UI 组件库（表单、布局、菜单、表格、消息提示等） |
| @element-plus/icons-vue | ^2.3.2 | Element Plus 官方图标库，已全局注册 |
| axios | ^1.20.0 | HTTP 请求库，已封装统一实例与拦截器 |
| marked | ^18.1.1 | Markdown 解析（AI 对话内容渲染，使用命名导出 `import { marked } from "marked"`） |
| dompurify | ^3.4.17 | HTML 消毒，防止 Markdown 渲染引入 XSS |

### 开发依赖（devDependencies）

| 依赖 | 版本 | 用途 |
| --- | --- | --- |
| vite | ^8.2.2 | 开发服务器与生产构建工具 |
| @vitejs/plugin-vue | ^6.0.8 | Vite 的 Vue 3 单文件组件支持 |
| vite-plugin-vue-devtools | ^8.2.1 | Vue DevTools 调试集成 |
| prettier | 3.9.6 | 代码格式化 |

### 环境要求

- Node.js：`^22.18.0` 或 `>=24.12.0`（见 package.json 的 engines 字段）
- 包管理：npm（仓库内含 package-lock.json；也可使用 pnpm / yarn）

## 二、目录结构

```
frontend/
├── index.html               # HTML 模板入口（页面标题：智能实验室预约系统）
├── package.json             # 依赖与 npm 脚本
├── .env.development         # 开发环境变量：VITE_API_BASE_URL 指向后端地址
├── vite.config.js           # Vite 配置：Vue 插件、DevTools、@ 路径别名
├── jsconfig.json            # IDE 路径提示，配置 @/* → ./src/*
├── .prettierrc.json         # Prettier 格式化配置
├── .npmrc                   # npm 配置
├── public/
│   └── favicon.ico          # 站点图标
└── src/
    ├── main.js              # 应用入口
    ├── App.vue              # 根组件
    ├── api/                 # 接口请求层
    │   ├── auth.js          # 认证接口（登录、注册）
    │   ├── user.js          # 用户接口（个人信息、修改密码、用户管理）
    │   ├── lab.js           # 实验室接口
    │   ├── equipment.js     # 设备接口
    │   ├── reservation.js   # 预约接口（创建、列表、审核、取消）
    │   ├── ai.js            # AI 对话接口（含 fetch 实现的 SSE 流式读取）
    │   └── file.js          # 文件上传接口
    ├── router/
    │   └── index.js         # 路由表（含登录态路由守卫）
    ├── layouts/
    │   └── Layout.vue       # 后台管理布局（顶栏 + 按角色渲染的侧边栏 + 内容区）
    ├── components/
    │   └── ReserveDialog.vue # 预约对话框（选择日期、起止时间、备注）
    ├── views/               # 页面级组件
    │   ├── Login.vue        # 登录页
    │   ├── Register.vue     # 注册页
    │   ├── Home.vue         # 系统首页（数据概览、快捷入口、最新预约）
    │   ├── AIChat.vue       # AI 智能助手（流式对话）
    │   ├── LabList.vue      # 实验室列表（学生浏览并发起预约）
    │   ├── LabEquipment.vue # 实验室下的设备列表（学生浏览并预约设备）
    │   ├── MyReservation.vue     # 我的预约（学生，支持取消）
    │   ├── Lab.vue          # 实验室管理（管理员增删改查）
    │   ├── Equipment.vue    # 设备管理（管理员增删改查）
    │   ├── AuditReservation.vue  # 预约审核管理（管理员通过 / 拒绝）
    │   ├── User.vue         # 用户管理（管理员增删改查）
    │   ├── Profile.vue      # 个人信息（含头像上传）
    │   └── Password.vue     # 修改密码
    ├── utils/               # 通用工具
    │   ├── request.js       # axios 实例 + 请求 / 响应拦截器
    │   ├── auth.js          # token / 用户信息的本地存储工具
    │   └── user.js          # useUser composable，管理登录用户响应式状态
    └── assets/
        ├── css/global.css   # 全局样式与基础重置
        └── imgs/logo.jpg    # 系统 Logo（同时用于顶栏与默认头像）
```

## 三、快速开始

```bash
# 安装依赖
npm install

# 启动开发服务器（热更新，默认地址 http://localhost:5173）
npm run dev

# 生产环境构建，产物输出到 dist/
npm run build

# 本地预览构建产物
npm run preview

# 使用 Prettier 格式化 src/ 下全部代码
npm run format
```

## 四、应用入口与全局配置

### 4.1 [index.html](index.html)

- `<div id="app">` 为 Vue 应用挂载点。
- 通过 `<script type="module" src="/src/main.js">` 引入入口脚本。
- 页面标题为「智能实验室预约系统」。

### 4.2 [src/main.js](src/main.js)

入口文件完成以下初始化工作：

1. 通过 `createApp(App)` 创建 Vue 应用实例；
2. `app.use(router)` 注册 Vue Router；
3. `app.use(ElementPlus, { locale: zhCn })` 全量注册 Element Plus，并设置为**简体中文**语言包；
4. 遍历 `@element-plus/icons-vue` 的所有导出，将图标**全局注册**为组件（模板中可直接使用 `<House />`、`<User />` 等）；
5. 引入全局样式 `@/assets/css/global.css`；
6. 挂载到 `#app`。

### 4.3 [src/App.vue](src/App.vue)

根组件只包含一个 `<router-view />`，所有页面均由路由出口渲染。

### 4.4 路径别名 `@`

在 [vite.config.js](vite.config.js) 与 [jsconfig.json](jsconfig.json) 中同步配置：

```
@  →  项目根目录/src
```

因此导入时可写 `import router from '@/router'`，构建与 IDE 智能提示均能识别。

## 五、路由说明

路由定义位于 [src/router/index.js](src/router/index.js)，使用 `createWebHistory`（History 模式），所有页面组件均采用**动态 import 懒加载**。

| 路径 | 路由名称 | 组件 | 说明 |
| --- | --- | --- | --- |
| `/` | — | — | 重定向到 `/manager/home` |
| `/login` | Login | views/Login.vue | 登录页（独立全屏页） |
| `/register` | Register | views/Register.vue | 注册页（独立全屏页） |
| `/manager` | Layout | layouts/Layout.vue | 后台布局容器，子路由渲染于其 `<router-view />` |
| `/manager/home` | Home | views/Home.vue | 系统首页 |
| `/manager/ai-chat` | AIChat | views/AIChat.vue | AI 智能助手 |
| `/manager/lablist` | LabList | views/LabList.vue | 实验室列表（学生） |
| `/manager/lab-equipment` | LabEquipment | views/LabEquipment.vue | 实验室设备列表（学生） |
| `/manager/my-reservation` | MyReservation | views/MyReservation.vue | 我的预约（学生） |
| `/manager/lab` | Lab | views/Lab.vue | 实验室管理（管理员） |
| `/manager/equipment` | Equipment | views/Equipment.vue | 设备管理（管理员） |
| `/manager/audit-reservation` | AuditReservation | views/AuditReservation.vue | 预约审核管理（管理员） |
| `/manager/user` | User | views/User.vue | 用户管理（管理员） |
| `/manager/profile` | Profile | views/Profile.vue | 个人信息 |
| `/manager/password` | Password | views/Password.vue | 修改密码 |

### 5.1 路由守卫（登录态校验）

[src/router/index.js](src/router/index.js) 通过 `router.beforeEach` 实现全局前置守卫：

```js
router.beforeEach((to, from) => {
    const token = getToken()
    if (to.path === '/login' || to.path === '/register') {
        return true          // 登录 / 注册页直接放行
    } else {
        return token ? true : '/login'   // 未登录访问受保护路由时跳转登录页
    }
})
```

- 仅依赖 `localStorage` 中的 token 是否存在判断登录态，**不校验 token 有效性**；若后端返回 401，由 axios 响应拦截器统一登出并跳转登录页。
- 登录 / 注册页不做拦截，其余路由均需 token。
- 页面级访问控制由侧边菜单按角色渲染（学生菜单不展示管理员入口）；后端接口另有 `get_current_admin` 依赖做最终权限拦截。

## 六、HTTP 请求层与工具层

### 6.1 环境变量（[.env.development](.env.development)）

```ini
VITE_API_BASE_URL=http://127.0.0.1:8000
```

前端请求后端的基础地址，由 [src/utils/request.js](src/utils/request.js) 中的 `import.meta.env.VITE_API_BASE_URL` 读取。生产环境可新增 `.env.production` 覆盖。

### 6.2 [src/utils/request.js](src/utils/request.js) —— axios 实例与拦截器

```js
const service = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    timeout: 30000
})
```

- **请求拦截器**：从 `localStorage` 读取 token，若存在则自动追加请求头 `Authorization: Bearer <token>`。
- **响应拦截器（成功分支）**：取出 `res.data`（后端统一响应 `{code, message, data}`）：
  - `code !== 200` 时用 `ElMessage.error` 提示后端返回的 `message`；
  - 若 `code === 401`，调用 `logout()` 清除本地凭据并跳转 `/login`，同时 `reject`；
  - 其余情况直接 `return data`，使调用方拿到的是后端响应体而非 axios 包裹对象。
- **响应拦截器（失败分支）**：
  - 有 `err.response` 且状态码为 401 → 提示「登录状态已失效」并登出跳转；
  - 其他 HTTP 错误 → 提示后端 `message` 或默认「请求失败」；
  - 无响应（网络异常 / 后端未启动）→ 提示「网络异常，请检查后端服务」。

### 6.3 [src/api/](src/api/) —— 接口请求层

业务接口函数统一放在 `src/api/` 下，按模块分文件，调用封装好的 `request` 实例：

| 文件 | 主要函数 |
| --- | --- |
| auth.js | `loginApi`、`registerApi` |
| user.js | `getUserInfo`、`updateUserInfo`、`updatePassword`、`getUserPageList`、`createUser`、`updateUser`、`deleteUser` |
| lab.js | `getLabPageList`、`getLab`、`createLab`、`updateLab`、`deleteLab` |
| equipment.js | `getEquipmentPageList`、`createEquipment`、`updateEquipment`、`deleteEquipment` |
| reservation.js | `createReservation`、`getReservationPageList`、`auditReservation`、`cancelReservation` |
| ai.js | `streamChatAPI`（SSE 流式对话） |
| file.js | `uploadFileApi`（FormData 上传） |

其中 [src/api/ai.js](src/api/ai.js) 的 `streamChatAPI(data, onEvent)` 由于需要读取 SSE 事件流，不使用 axios，而是基于原生 `fetch` 实现：

- 手动拼接 `Authorization` 请求头发起 POST 请求；
- 校验 401（抛出「token过期，请重新登录」）与 `Content-Type: text/event-stream`；
- 通过 `res.body.getReader()` 逐块读取，按 `\n\n` 切分事件、提取 `data:` 行并 `JSON.parse`，回调给调用方（AIChat.vue）处理。

### 6.4 [src/utils/auth.js](src/utils/auth.js) —— 本地存储工具

基于 `localStorage` 管理登录凭据：

| 方法 | 作用 |
| --- | --- |
| `getToken()` / `setToken(token)` / `removeToken()` | 读取 / 写入 / 删除 `token` |
| `getUserInfo()` / `setUserInfo(user)` / `removeUserInfon()` | 读取 / 写入 / 删除 `userInfo`（JSON 序列化） |
| `logout()` | 清除 token 与 userInfo（退出登录） |

> 注意：`removeUserInfon` 命名拼写有误（多了 `n`），调用时需保持一致。

### 6.5 [src/utils/user.js](src/utils/user.js) —— useUser composable

```js
const userInfo = ref(getUserInfo())   // 响应式，从 localStorage 初始化

export function useUser() {
    return { userInfo, saveLoginData, updateUser, reloadUser }
}
```

- `saveLoginData({ token, user })`：登录成功后一次性写入 token 与用户信息，并更新响应式 `userInfo`。
- `updateUser(user)`：仅更新用户信息。
- `reloadUser()`：从 localStorage 重新读取并刷新 `userInfo`。
- `userInfo` 为模块级 `ref`，所有调用 `useUser()` 的组件共享同一份响应式状态。

## 七、页面与组件说明

### 7.1 [Layout.vue](src/layouts/Layout.vue) —— 后台整体布局

基于 Element Plus 容器组件实现经典后台结构：

- **el-header（顶栏）**：左侧 Logo 与系统名称「智能实验室预约系统」；右侧用户头像 + 用户名的下拉菜单，含「个人信息」「退出登录」「修改密码」三项。
- **el-aside（侧边栏，宽 200px）**：`el-menu` 开启 `router` 属性，菜单项 `index` 即跳转路径，并按 `userInfo.role` 动态渲染：
  - 公共：系统首页（`/manager/home`）、AI智能助手（`/manager/ai-chat`）；
  - 学生（role === 'student'）：实验室列表（`/manager/lablist`）、我的预约（`/manager/my-reservation`）；
  - 管理员（role === 'admin'）：实验室管理（`/manager/lab`）、设备管理（`/manager/equipment`）、预约审核管理（`/manager/audit-reservation`）、用户管理（`/manager/user`）。
- **el-main（内容区）**：通过 `<router-view />` 渲染子路由页面。

### 7.2 [Login.vue](src/views/Login.vue) / [Register.vue](src/views/Register.vue) —— 登录 / 注册页

- 居中卡片式布局，登录页标题「实验室预约系统」，副标题「基于Agent智能实验室预约系统」。
- 登录页调用 `loginApi(form)`，成功（`res.code === 200`）后通过 `useUser().saveLoginData(res.data)` 写入 token 与用户信息，跳转 `/manager/home`；失败由 axios 响应拦截器统一弹出后端 message。
- 注册页包含账号、密码、确认密码三个输入框，校验两次密码一致后调用 `registerApi`，成功跳转登录页。

### 7.3 [Home.vue](src/views/Home.vue) —— 系统首页

工作台风格首页，按角色差异化展示：

- **欢迎横幅**：按时段问候（早上好 / 下午好等），展示当前日期与用户角色标签；
- **数据统计卡片**：管理员可见「实验室总数 / 预约总数 / 待审核预约 / 用户总数」，学生可见「实验室总数 / 我的预约 / 待审核 / 已通过」（数据来自各分页接口的 total）；
- **快捷入口**：按角色展示常用页面入口卡片；
- **最新预约**：展示最近 5 条预约记录（实验室、日期、时段、状态标签），「查看更多」按角色跳转审核页或我的预约页。

### 7.4 [AIChat.vue](src/views/AIChat.vue) —— AI 智能助手

- 聊天气泡布局（用户靠右、助手靠左），消息区固定高度自动滚动到底部。
- 通过 `streamChatAPI` 发起 SSE 流式对话，实时处理后端事件：
  - `status` → 更新助手气泡顶部的状态提示；
  - `tool_start` / `tool_end` → 在气泡内以步骤列表展示工具调用过程（开始 / 完成 / 输出结果预览）；
  - `token` → 增量追加到助手消息内容，实现打字机效果；
  - `error` → 弹出错误提示并展示错误内容。
- 助手消息内容使用 `marked.parse` 渲染 Markdown，并经 `DOMPurify.sanitize` 消毒后以 `v-html` 输出，防止 XSS。
- 输入框为 textarea，Enter 发送、Shift+Enter 换行；发送期间按钮 loading，防止重复提交。

### 7.5 [LabList.vue](src/views/LabList.vue) / [LabEquipment.vue](src/views/LabEquipment.vue) —— 实验室 / 设备浏览（学生）

- 实验室列表：卡片式展示实验室封面、名称、位置、容量、开放时段，支持按名称模糊查询；点击「预约」打开 [ReserveDialog.vue](src/components/ReserveDialog.vue) 提交预约；点击「查看设备」进入实验室设备列表。
- 设备列表：展示指定实验室下的设备（图片、名称、规格、数量、状态），可针对单台设备发起预约（提交时携带 equipment_id）。

### 7.6 [ReserveDialog.vue](src/components/ReserveDialog.vue) —— 预约对话框

可复用的预约表单组件（`visible` 通过 `v-model:visible` 控制，props 接收实验室 / 设备信息，事件 `success` 通知父组件刷新）：选择预约日期（禁用过去日期）、开始 / 结束时间、填写备注，提交时调用 `createReservation`，成功提示「预约成功，请等待管理员审核」。

### 7.7 [MyReservation.vue](src/views/MyReservation.vue) —— 我的预约（学生）

分页表格展示本人预约记录（类型、实验室 / 设备、日期、时段、备注、状态），支持按状态筛选；「待审核」状态的记录可点击取消（调用 `cancelReservation`）。

### 7.8 [Lab.vue](src/views/Lab.vue) / [Equipment.vue](src/views/Equipment.vue) —— 实验室 / 设备管理（管理员）

- 表格分页展示 + 名称关键字模糊查询（设备页额外支持按实验室筛选）；
- 新增 / 编辑使用对话框表单：实验室含名称、简介、封面（上传）、位置、容量、开放 / 关闭时间、状态；设备含所属实验室、名称、简介、图片（上传）、规格、数量、状态；
- 删除前二次确认；图片 / 封面上传复用 `uploadFileApi`，上传后回显。

### 7.9 [AuditReservation.vue](src/views/AuditReservation.vue) —— 预约审核管理（管理员）

分页表格展示全部用户的预约记录（含预约人），支持按状态筛选；「待审核」状态的记录可执行「通过」或「拒绝」（调用 `auditReservation`，status 分别为 1 / 2），操作前二次确认。

### 7.10 [User.vue](src/views/User.vue) —— 用户管理（管理员）

用户分页表格（账号或名称模糊查询），新增 / 编辑对话框包含账号（编辑时禁用）、密码、名称、角色（student / admin）、邮箱、手机号、状态；支持删除用户（后端限制不可删除自己）。

### 7.11 [Profile.vue](src/views/Profile.vue) / [Password.vue](src/views/Password.vue) —— 个人信息 / 修改密码

- 个人信息页：账号只读，可修改名称、邮箱、手机号、头像（上传），保存调用 `updateUserInfo` 并同步 `useUser` 响应式状态；
- 修改密码页：输入原密码、新密码、确认新密码，校验两次一致后调用 `updatePassword`，成功后登出并跳转登录页。

## 八、样式说明

[src/assets/css/global.css](src/assets/css/global.css) 为全局基础样式，在 main.js 中全局引入：

- 全局 `box-sizing: border-box`；
- 重置 `html / body / #app` 的宽高与内外边距；
- body 字体为「Microsoft YaHei」，14px，文字色 `#303133`，背景色 `#f5f7fa`（Element Plus 常用浅灰背景）；
- 清除标题（h1~h6）、段落、列表的默认边距与列表样式；
- 链接继承颜色且无下划线；图片 `max-width: 100%`。
- 额外重置 `.el-tooltip__trigger { outline: none }`，去除 Element Plus tooltip 触发元素的聚焦外轮廓。

各页面组件的布局样式使用 `<style scoped>` 局部作用域，不会污染全局。

## 九、构建配置（vite.config.js）

```js
export default defineConfig({
  plugins: [
    vue(),              // 支持 .vue 单文件组件
    vueDevTools(),      // 集成 Vue DevTools
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),  // @ 指向 src
    },
  },
})
```

跨域由后端 CORS 中间件处理（允许 `localhost:5173` / `127.0.0.1:5173` 携带凭证），前端通过 `.env.development` 的 `VITE_API_BASE_URL` 直接请求后端，**无需配置 Vite 开发代理**。
