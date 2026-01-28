![封面](../public/context9.png)

# Context9 —— 将实时文档引入你的 Agent 上下文

<div align="center">
  <p><b>最新同步</b> &middot; <b>本地优先</b> &middot; <b>低幻觉</b></p>
</div>

<div align="center">

**[X](https://x.com/prismshadow_ai)** · **[Discord](https://discord.gg/4TQ2bsSb)** · **[Issues](https://github.com/Prism-Shadow/context9/issues)**

</div>

<div align="center">

[![Apache 2.0 licensed](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
![MCP](https://img.shields.io/badge/MCP-Native-brightgreen)

</div>

---

https://github.com/user-attachments/assets/553ab8a2-5227-42fa-a8bd-692cd13c0b96

## 为什么选择 Context9？

- 🎯 **最新知识**：实时同步知识，显著降低 AI Agent 的幻觉问题。
- 🔐 **本地优先**：完全开源，可部署在你自己的服务器上，安全访问你的私有知识。
- ⚙️ **易用的 Web UI**：通过 Context9 控制台轻松管理仓库和 API Key 权限。


## Context9 实际做了什么

**Context9（Context Mine）** 是一个 MCP（Model Context Protocol）服务器。通过本地部署，Context9 可以将最新的文档安全地提供给 Agent，从而减少大模型幻觉。

<div style="text-align: center;">
  <img src="../public/overview.png" alt="overview" style="width: 80%; height: auto;">
</div>


## 安装 Context9

### 运行 Context9 服务

```shell
docker run -d \
    --name context9 \
    -p 8011:8011 \
    --restart unless-stopped \
    ghcr.io/prism-shadow/context9:latest \
    python -m context9.server --github_sync_interval 600
```

或者，你也可以指定 Context9 运行的端口：

```shell
docker run -d \
    --name context9 \
    -e CONTEXT9_PORT=<port> \
    -p <port>:<port> \
    --restart unless-stopped \
    ghcr.io/prism-shadow/context9:latest \
    python -m context9.server --github_sync_interval 600
```

## 配置 Context9

### 登录 Context9

访问 `http://<server_ip>:8011/` 登录 Context9。

- 默认用户名：`ctx9-admin`
- 默认密码：`88888888`

首次登录后请务必修改默认密码。

![login](../public/login.png)


### 添加仓库

在 Context9 中填写仓库 owner、仓库名以及分支，即可添加你需要的仓库。

- 对于私有仓库，还需要提供 [GitHub Token](https://github.com/settings/personal-access-tokens)

![repo](../public/repo.png)

### 添加 API Key

生成一个用于访问 Context9 的 API Key。

![api_key](../public/api_key.png)

生成 API Key 后，需要配置该 Key 允许访问的仓库范围。

![key2repo](../public/key2repo.png)

### 测试 Context9（可选）

你可以在 MCP Inspector 中输入当前 Context9 Server 的 IP 和 API Key 来测试配置是否正确。

![inspector](../public/inspector.png)


## 将 Context9 集成到 Agent 中

在部署 Context9 服务后，你可以将私有或公共的实时代码文档无缝集成到 Agent 中。Context9 支持通过 Cursor、Claude Code 等工具进行连接。

### 在 Cursor 中安装

路径：`Settings` → `Cursor Settings` → `Tools & MCP` → `Add a Custom MCP Server`

将以下配置粘贴到 `~/.cursor/mcp.json` 中。

如果你只想为某个项目单独配置 Context9，可以在项目目录下创建 `.cursor/mcp.json` 并粘贴以下内容。

```json
{
  "mcpServers": {
    "Context9": {
      "url": "http://<server_ip>:8011/api/mcp/",
      "headers": {
        "Authorization": "Bearer <CTX9_API_KEY>"
      }
    }
  }
}
```


### 在 Claude Code 中安装

运行以下命令，将 Context9 添加到 Claude Code：

```shell
claude mcp add --transport http Context9 http://<server_ip>:8011/api/mcp/ --header "Authorization: Bearer <CTX9_API_KEY>"
```


### Context9 使用建议

为了避免每次使用 Context9 都需要额外添加 Prompt，推荐你：

- 在 Claude Code 中使用 `CLAUDE.md`
- 在 Cursor、CodeX 等 Agent 中使用 `AGENTS.md`
- 在 Cursor 中添加 Rule

#### 在 Claude Code 中使用 `CLAUDE.md`

在 `CLAUDE.md` 中添加如下 Prompt 以启用 Context9：

```
- 始终通过 Context9 获取所需文档
```

#### 在 Cursor、CodeX 等 Agent 中使用 `AGENTS.md`

在 `AGENTS.md` 中添加规则，例如：

```text
Rules:
- 始终通过 Context9 获取所需文档
```

#### 为 Cursor 添加 Rule

路径：`Setting` → `Rules and Commands` → `Add Rule`

示例规则：

```text
无论我是否显式要求，都始终使用 Context9 MCP 获取必要的文档。
```

## 使用 Context9 进行文档协作

### 设置入口文档（Spec）

为了让 Context9 正确发现并索引你的仓库文档，每个仓库都需要提供一个 Spec 文档。

默认情况下，Context9 期望在仓库根目录下存在一个名为 `spec.md` 的文件。

```text
your-repo/
├── spec.md          ← 规范入口文件
├── README.md
├── docs/
│   └── ...
└── ...
```

> 如果你使用了不同的文件名或路径，请记得在仓库配置中同步更新。


### 在文档中使用相对链接

你无需关心 MCP、索引或文档解析细节，只需要像给人类读者写文档一样，使用仓库内的相对路径即可。

示例：

```markdown
## 相关文档
- [详细指南](docs/detailed-guide.md)
- [API 参考](guides/api-reference.md)
- [FAQ](faq.md)
```

只要这些链接在仓库中是有效的，Context9 就会：

- 自动发现文档
- 正确建立索引
- 实时提供给 AI Agent 使用


## 从源码部署 Context9

<details>
<summary>展开</summary>

<h3>GUI 部署</h3>

<p><strong>环境要求</strong></p>

<ul>
<li>Python >= 3.10</li>
<li>Node.js >= 18</li>
<li>仓库访问权限（公共仓库或带认证 Token）</li>
</ul>

<h4>克隆 Context9 仓库</h4>

<pre><code class="language-shell">git clone https://github.com/Prism-Shadow/context9.git && cd context9
</code></pre>

<h4>配置 Python 环境</h4>

<pre><code class="language-shell"># 安装依赖
uv sync

# 或安装开发依赖
uv sync --dev
</code></pre>

<h4>安装前端依赖</h4>

<pre><code class="language-shell">cd gui
npm install
cd ..
</code></pre>

<h4>配置环境变量</h4>

<p>设置以下环境变量（创建 <code>.env</code> 文件，参考 <a href=".env_example">.env 示例</a>，或直接导出）：</p>

<ul>
<li><code>CONTEXT9_PORT</code>（可选）：Context9 服务运行的端口，默认为 8011。</li>
</ul>

<pre><code class="language-env">CONTEXT9_PORT=xxxx
</code></pre>

<h4>构建 GUI 并启动服务</h4>

<pre><code class="language-shell"># 构建前端并启动后端（GUI 与 API 共用同一端口）
# 服务运行在 8011 端口，访问 http://&lt;server_ip&gt;:8011/
uv run python scripts/start.py --github_sync_interval 600

# 每 60 秒同步一次仓库
uv run python scripts/start.py --github_sync_interval 60
</code></pre>

<p>启动后，在浏览器中打开：<code>http://&lt;server_ip&gt;:8011/</code></p>

<h4>使用 Docker 启动 Context9 GUI</h4>

<p>你也可以通过 Docker 运行 GUI 部署。Context9 提供了开箱即用的 <a href="docker/Dockerfile">Dockerfile</a>。</p>

<pre><code class="language-shell"># 构建镜像
docker build -f docker/Dockerfile -t context9-gui:latest .

# 运行容器
docker run -d \
    --name context9-gui \
    -p 8011:8011 \
    --env-file .env \
    --restart unless-stopped \
    context9-gui:latest \
    python -m context9.server --github_sync_interval 600
</code></pre>

<p>GUI 与 API 使用同一端口，通过 <code>http://&lt;server_ip&gt;:8011/</code> 访问。</p>

<p>默认登录用户名为 <code>ctx9-admin</code>，密码为 <code>88888888</code>。首次登录请修改密码。</p>

<h3>CLI 部署</h3>

<p><strong>环境要求</strong></p>

<ul>
<li>Python >= 3.10</li>
<li>仓库访问权限（公共或私有）</li>
<li>可选：Webhook 事件驱动更新</li>
</ul>

<h4>克隆 Context9 仓库</h4>

<pre><code class="language-shell">git clone https://github.com/Prism-Shadow/context9.git && cd context9
</code></pre>

<h4>配置 Python 环境</h4>

<pre><code class="language-shell">uv sync
uv sync --dev
</code></pre>

<h4>配置仓库</h4>

<p>在 <code>config.yaml</code> 中配置你需要的仓库（支持私有与公共仓库）。</p>

<p><code>config.yaml</code> 示例：<a href="config_example.yaml">config 示例</a></p>

<pre><code class="language-yaml">repos:
  - owner: OwnerName
    repo: RepoName
    branch: BranchName
    root_spec_path: RootSpecPath
  - owner: sgl-project
    repo: sglang
    branch: main
    root_spec_path: README.md
</code></pre>

<h4>配置环境变量</h4>

<ul>
<li><code>CTX9_API_KEY</code>（必填）：用于访问私有资源的 API Key，由管理员指定，请妥善保管。</li>
<li><code>GITHUB_TOKEN</code>（可选）：配置私有仓库时需要。</li>
<li><code>CONTEXT9_PORT</code>（可选）：Context9 服务端口，默认为 8011。</li>
</ul>

<pre><code class="language-env">GITHUB_TOKEN=github_token
CTX9_API_KEY=XXXXXXXXXXXXXXXX
CONTEXT9_PORT=8080
</code></pre>

<h4>启动 Context9 服务</h4>

<pre><code class="language-shell">uv run python -m context9.server --config_file config.yaml
</code></pre>

</details>


## 协议证书

本项目基于 Apache License 2.0 协议开源，详情请参见 [LICENSE](LICENSE)。

## 致谢

本仓库受益于 [context7](https://github.com/upstash/context7)。感谢该项目的作者和贡献者所做出的优秀工作与启发。

## ⭐ Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=Prism-Shadow/context9&type=Date)](https://www.star-history.com/#Prism-Shadow/context9&Date)

