![カバー](../public/context9.png)

# Context9 —— リアルタイムドキュメントを Agent のコンテキストへ

<div align="center">
  <p><b>最新同期</b> &middot; <b>ローカルファースト</b> &middot; <b>低ハルシネーション</b></p>
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

## なぜ Context9 なのか？

- 🎯 **最新ドキュメント**：ドキュメントをリアルタイムで同期し、AI Agent のハルシネーションを大幅に低減します。
- 🔐 **ローカルファースト**：完全オープンソース。自分のサーバーにデプロイでき、プライベートな知識を安全に利用できます。
- ⚙️ **使いやすい Web UI**：Context9 パネルからリポジトリや API Key の権限を簡単に管理できます。


## Context9 は何をするのか

**Context9（Context Mine）** は MCP（Model Context Protocol）サーバーです。ローカル環境にデプロイすることで、最新のドキュメントを安全に Agent へ提供し、LLM のハルシネーションを抑制します。

<div style="text-align: center;">
  <img src="../public/overview.png" alt="overview" style="width: 80%; height: auto;">
</div>


## Context9 のインストール

### Context9 サーバーの起動

```shell
docker run -d \
    --name context9 \
    -p 8011:8011 \
    --restart unless-stopped \
    ghcr.io/prism-shadow/context9:latest \
    python -m context9.server --github_sync_interval 600
```

または、Context9 が使用するポートを指定することもできます。

```shell
docker run -d \
    --name context9 \
    -e CONTEXT9_PORT=<port> \
    -p <port>:<port> \
    --restart unless-stopped \
    ghcr.io/prism-shadow/context9:latest \
    python -m context9.server --github_sync_interval 600
```

## Context9 の設定

### Context9 にログイン

`http://<server_ip>:8011/` にアクセスして Context9 にログインします。

- デフォルトユーザー名：`ctx9-admin`
- デフォルトパスワード：`88888888`

初回ログイン後、必ずパスワードを変更してください。

![login](../public/login.png)


### リポジトリの追加

リポジトリの owner、リポジトリ名、ブランチを入力して、必要なリポジトリを追加します。

- プライベートリポジトリの場合は [GitHub Token](https://github.com/settings/personal-access-tokens) が必要です。

![repo](../public/repo.png)

### API Key の追加

Context9 にアクセスするための API Key を生成します。

![api_key](../public/api_key.png)

API Key を生成した後、その Key がアクセス可能なリポジトリを設定してください。

![key2repo](../public/key2repo.png)

### Context9 のテスト（任意）

MCP Inspector に Context9 サーバーの IP と API Key を入力して、設定をテストできます。

![inspector](../public/inspector.png)


## Agent への Context9 の統合

Context9 をデプロイすると、プライベートおよびパブリックな最新コードドキュメントを Agent にシームレスに統合できます。Cursor や Claude Code などのツールから接続可能です。

### Cursor へのインストール

手順：`Settings` → `Cursor Settings` → `Tools & MCP` → `Add a Custom MCP Server`

以下の設定を `~/.cursor/mcp.json` に貼り付けてください。

プロジェクト単位で設定したい場合は、プロジェクトディレクトリに `.cursor/mcp.json` を作成してください。

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


### Claude Code へのインストール

以下のコマンドを実行して、Context9 を Claude Code に追加します。

```shell
claude mcp add --transport http Context9 http://<server_ip>:8011/api/mcp/ --header "Authorization: Bearer <CTX9_API_KEY>"
```


### Context9 利用のおすすめ設定

Context9 を毎回明示的に指定しなくても使えるよう、以下を推奨します。

- Claude Code では `CLAUDE.md` を使用
- Cursor や CodeX などでは `AGENTS.md` を使用
- Cursor に Rule を追加

#### Claude Code で `CLAUDE.md` を使用

`CLAUDE.md` に以下を追加してください。

```
- 常に Context9 経由で必要なドキュメントを取得する
```

#### Cursor / CodeX 用 `AGENTS.md`

`AGENTS.md` に以下のようなルールを追加します。

```text
Rules:
- 常に Context9 経由で必要なドキュメントを取得する
```

#### Cursor に Rule を追加

手順：`Setting` → `Rules and Commands` → `Add Rule`

例：

```text
明示的に指示されていなくても、常に Context9 MCP を使用して必要なドキュメントを取得する。
```

## Context9 でのドキュメント運用

### エントリードキュメント（Spec）の設定

Context9 がリポジトリ内のドキュメントを正しく検出・インデックスするために、各リポジトリには Spec ドキュメントを用意してください。

デフォルトでは、リポジトリのルートに `spec.md` を配置します。

```text
your-repo/
├── spec.md          ← 仕様書エントリーポイント
├── README.md
├── docs/
│   └── ...
└── ...
```

> ファイル名やパスを変更する場合は、リポジトリ設定も忘れずに更新してください。


### ドキュメント内での相対リンク

MCP やインデックスの仕組みを意識する必要はありません。通常のリポジトリ相対パスでリンクを記述するだけで問題ありません。

例：

```markdown
## 関連ドキュメント
- [詳細ガイド](docs/detailed-guide.md)
- [API リファレンス](guides/api-reference.md)
- [FAQ](faq.md)
```

これらのリンクが有効であれば、Context9 は以下を自動で行います。

- ドキュメントの検出
- 正確なインデックス作成
- AI Agent へのリアルタイム提供


## ソースコードから Context9 をデプロイ

<details>
<summary>展開</summary>

<h3>GUI デプロイ</h3>

<p><strong>要件</strong></p>

<ul>
<li>Python >= 3.10</li>
<li>Node.js >= 18</li>
<li>リポジトリアクセス（公開または認証 Token）</li>
</ul>

<h4>Context9 リポジトリのクローン</h4>

<pre><code class="language-shell">git clone https://github.com/Prism-Shadow/context9.git && cd context9
</code></pre>

<h4>Python 環境のセットアップ</h4>

<pre><code class="language-shell">uv sync
uv sync --dev
</code></pre>

<h4>フロントエンド依存関係のインストール</h4>

<pre><code class="language-shell">cd gui
npm install
cd ..
</code></pre>

<h4>環境変数の設定</h4>

<ul>
<li><code>CONTEXT9_PORT</code>（任意）：Context9 サービスのポート（デフォルト 8011）</li>
</ul>

<pre><code class="language-env">CONTEXT9_PORT=xxxx
</code></pre>

<h4>GUI をビルドしてサーバー起動</h4>

<pre><code class="language-shell">uv run python scripts/start.py --github_sync_interval 600
uv run python scripts/start.py --github_sync_interval 60
</code></pre>

<h3>CLI デプロイ</h3>

<p><strong>要件</strong></p>

<ul>
<li>Python >= 3.10</li>
<li>リポジトリアクセス権限</li>
</ul>

</details>


## ライセンス

本プロジェクトは Apache License 2.0 のもとで公開されています。詳細は [LICENSE](LICENSE) を参照してください。

## 謝辞

本リポジトリは [context7](https://github.com/upstash/context7) から恩恵を受けています。素晴らしい成果とインスピレーションを提供してくださった作者およびコントリビューターの皆様に感謝します。


## ⭐ Star 履歴

[![Star History Chart](https://api.star-history.com/svg?repos=Prism-Shadow/context9&type=date&legend=top-left)](https://www.star-history.com/#Prism-Shadow/context9&type=date&legend=top-left)

