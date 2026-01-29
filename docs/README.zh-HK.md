![封面](../public/context9.png)

# Context9 —— 將即時文件引入你的 Agent 上下文

<div align="center">
  <p><b>即時同步</b> &middot; <b>本地優先</b> &middot; <b>低幻覺</b></p>
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

## 為什麼選擇 Context9？

- 🎯 **即時知識**：即時同步文件內容，大幅降低 AI Agent 的幻覺問題。
- 🔐 **本地優先**：完全開源，可部署於你自己的伺服器，安全存取私有知識。
- ⚙️ **好用的 Web UI**：透過 Context9 管理介面輕鬆管理儲存庫與 API Key 權限。


## Context9 實際做了什麼

**Context9（Context Mine）** 是一個 MCP（Model Context Protocol）伺服器。透過本地部署，Context9 能安全地將最新文件提供給 Agent，進而降低大型語言模型的幻覺。

<div style="text-align: center;">
  <img src="../public/overview.png" alt="overview" style="width: 80%; height: auto;">
</div>


## 安裝 Context9

### 執行 Context9 服務

```shell
docker run -d \
    --name context9 \
    -p 8011:8011 \
    --restart unless-stopped \
    ghcr.io/prism-shadow/context9:latest \
    python -m context9.server --github_sync_interval 600
```

或者，你也可以指定 Context9 執行的連接埠：

```shell
docker run -d \
    --name context9 \
    -e CONTEXT9_PORT=<port> \
    -p <port>:<port> \
    --restart unless-stopped \
    ghcr.io/prism-shadow/context9:latest \
    python -m context9.server --github_sync_interval 600
```

## 設定 Context9

### 登入 Context9

造訪 `http://<server_ip>:8011/` 登入 Context9。

- 預設使用者名稱：`ctx9-admin`
- 預設密碼：`88888888`

首次登入後請務必修改預設密碼。

![login](../public/login.png)


### 新增儲存庫

在 Context9 中填寫儲存庫擁有者（owner）、儲存庫名稱與分支，即可新增所需的儲存庫。

- 私有儲存庫需要額外提供 [GitHub Token](https://github.com/settings/personal-access-tokens)

![repo](../public/repo.png)

### 新增 API Key

產生一組用於存取 Context9 的 API Key。

![api_key](../public/api_key.png)

產生 API Key 後，需要設定該 Key 可存取的儲存庫範圍。

![key2repo](../public/key2repo.png)

### 測試 Context9（選用）

你可以在 MCP Inspector 中輸入目前 Context9 伺服器的 IP 與 API Key，以測試設定是否正確。

![inspector](../public/inspector.png)


## 將 Context9 整合至 Agent

部署 Context9 服務後，你可以將私有或公開的即時程式碼文件無縫整合至 Agent 中。Context9 可與 Cursor、Claude Code 等工具搭配使用。

### 在 Cursor 中安裝

路徑：`Settings` → `Cursor Settings` → `Tools & MCP` → `Add a Custom MCP Server`

將以下設定貼入 `~/.cursor/mcp.json`。

若只想針對單一專案設定 Context9，可在專案目錄中建立 `.cursor/mcp.json` 並貼上以下內容。

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


### 在 Claude Code 中安裝

執行以下指令，將 Context9 加入 Claude Code：

```shell
claude mcp add --transport http Context9 http://<server_ip>:8011/api/mcp/ --header "Authorization: Bearer <CTX9_API_KEY>"
```


### Context9 使用建議

為了避免每次使用 Context9 都需要額外加入 Prompt，建議你：

- 在 Claude Code 中使用 `CLAUDE.md`
- 在 Cursor、CodeX 等 Agent 中使用 `AGENTS.md`
- 在 Cursor 中新增 Rule

#### 在 Claude Code 中使用 `CLAUDE.md`

在 `CLAUDE.md` 中加入以下 Prompt 以啟用 Context9：

```
- 永遠透過 Context9 取得所需文件
```

#### 在 Cursor、CodeX 等 Agent 中使用 `AGENTS.md`

在 `AGENTS.md` 中新增規則，例如：

```text
Rules:
- 永遠透過 Context9 取得所需文件
```

#### 為 Cursor 新增 Rule

路徑：`Setting` → `Rules and Commands` → `Add Rule`

範例規則：

```text
無論我是否明確要求，都一律使用 Context9 MCP 取得必要文件。
```

## 使用 Context9 進行文件協作

### 設定入口文件（Spec）

為了讓 Context9 能正確發現並索引你的儲存庫文件，每個儲存庫都應提供一份 Spec 文件。

預設情況下，Context9 會在儲存庫根目錄尋找名為 `spec.md` 的檔案。

```text
your-repo/
├── spec.md          ← 規格入口文件
├── README.md
├── docs/
│   └── ...
└── ...
```

> 若你使用不同的檔名或路徑，請記得同步更新儲存庫設定。


### 在文件中使用相對連結

你無需關心 MCP、索引或文件解析細節，只要像為人類讀者撰寫文件一樣，使用儲存庫內的相對路徑即可。

範例：

```markdown
## 相關文件
- [詳細指南](docs/detailed-guide.md)
- [API 參考](guides/api-reference.md)
- [FAQ](faq.md)
```

只要這些連結在儲存庫中是有效的，Context9 就會：

- 自動發現文件
- 正確建立索引
- 即時提供給 AI Agent 使用


## 從原始碼部署 Context9

<details>
<summary>展開</summary>

<h3>GUI 部署</h3>

<p><strong>環境需求</strong></p>

<ul>
<li>Python >= 3.10</li>
<li>Node.js >= 18</li>
<li>儲存庫存取權限（公開或含驗證 Token）</li>
</ul>

<h4>複製 Context9 儲存庫</h4>

<pre><code class="language-shell">git clone https://github.com/Prism-Shadow/context9.git && cd context9
</code></pre>

<h4>設定 Python 環境</h4>

<pre><code class="language-shell">uv sync
uv sync --dev
</code></pre>

<h4>安裝前端相依套件</h4>

<pre><code class="language-shell">cd gui
npm install
cd ..
</code></pre>

<h4>設定環境變數</h4>

<ul>
<li><code>CONTEXT9_PORT</code>（選用）：Context9 服務執行的連接埠，預設為 8011。</li>
</ul>

<pre><code class="language-env">CONTEXT9_PORT=xxxx
</code></pre>

<h4>建置 GUI 並啟動服務</h4>

<pre><code class="language-shell">uv run python scripts/start.py --github_sync_interval 600
uv run python scripts/start.py --github_sync_interval 60
</code></pre>

<h3>CLI 部署</h3>

<p><strong>環境需求</strong></p>

<ul>
<li>Python >= 3.10</li>
<li>儲存庫存取權限</li>
</ul>

</details>


## 授權條款

本專案依 Apache License 2.0 授權釋出，詳情請參閱 [LICENSE](LICENSE)。

## 致謝

本倉庫受益於 [context7](https://github.com/upstash/context7)。感謝該專案的作者與貢獻者所帶來的優秀工作與啟發。


## ⭐ Star 歷史

[![Star History Chart](https://api.star-history.com/svg?repos=Prism-Shadow/context9&type=date&legend=top-left)](https://www.star-history.com/#Prism-Shadow/context9&type=date&legend=top-left)

