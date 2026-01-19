# Context9 前端管理后台

这是 Context9 的管理后台前端应用，用于管理 API Keys、仓库配置以及访问权限。

## 技术栈

- **React 18+**: 前端框架
- **TypeScript**: 类型安全
- **Vite**: 构建工具
- **Tailwind CSS 3**: 样式框架
- **React Router v6**: 路由管理
- **React Hook Form**: 表单处理
- **Axios**: HTTP 客户端

## 开发

### 安装依赖

```bash
cd gui
npm install
```

### 启动开发服务器

```bash
npm run dev
```

开发服务器将在 `http://localhost:3000` 启动。

### 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

### 预览生产构建

```bash
npm run preview
```

## 环境变量

创建 `.env` 文件（已提供 `.env` 示例）：

```env
VITE_API_BASE_URL=http://localhost:8011
```

## 项目结构

```
gui/
├── public/                 # 静态资源
├── src/
│   ├── components/         # 可复用组件
│   │   ├── common/         # 通用组件（Button, Input, Modal, Table）
│   │   └── layout/          # 布局组件（Header, Sidebar, Layout）
│   ├── pages/              # 页面组件
│   │   ├── Login.tsx       # 登录页
│   │   ├── Dashboard.tsx   # 仪表盘
│   │   ├── ApiKeys.tsx     # API Key 管理页
│   │   ├── ApiKeyDetail.tsx # API Key 详情/权限管理页
│   │   └── Repositories.tsx # 仓库管理页
│   ├── services/           # API 服务层
│   │   ├── api.ts          # Axios 实例配置
│   │   ├── auth.ts         # 认证相关 API
│   │   ├── apiKeys.ts      # API Key 相关 API
│   │   └── repositories.ts # 仓库相关 API
│   ├── contexts/           # React Context
│   │   └── AuthContext.tsx # 认证上下文
│   ├── utils/              # 工具函数
│   │   ├── constants.ts    # 常量定义
│   │   ├── helpers.ts      # 辅助函数
│   │   └── types.ts        # TypeScript 类型定义
│   ├── App.tsx             # 根组件
│   ├── main.tsx            # 入口文件
│   └── index.css           # 全局样式（Tailwind 导入）
├── tailwind.config.js      # Tailwind 配置
├── vite.config.ts          # Vite 配置
├── tsconfig.json           # TypeScript 配置
└── package.json            # 依赖管理
```

## 功能

### 1. 管理员登录
- 基于会话的管理员身份验证
- JWT Token 管理

### 2. API Key 管理
- 创建、删除、命名 API Keys
- 编辑 API Key 名称
- 管理 API Key 权限（分配可访问的仓库）

### 3. 仓库配置管理
- 增加、删除、编辑仓库配置（owner, repo, branch, root_spec_path）
- GitHub Token 管理：
  - 设置 GitHub Token
  - 更新 GitHub Token
  - 删除 GitHub Token
  - 验证 GitHub Token

## API 集成

前端通过以下 API 端点与后端通信：

- `/api/admin/login` - 管理员登录
- `/api/admin/me` - 获取当前管理员信息
- `/api/admin/logout` - 登出
- `/api/admin/api-keys` - API Key 管理
- `/api/admin/repositories` - 仓库管理

详细 API 文档请参考 `FRONTEND_DEVELOPMENT.md`。

## 注意事项

1. **Token 安全**: GitHub Token 和 API Key 仅在创建/更新时返回一次明文，请妥善保存。
2. **认证**: 所有受保护的路由都需要有效的 JWT Token。
3. **CORS**: 开发环境下，Vite 代理已配置为转发 `/api` 请求到后端服务器。
