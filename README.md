![Cover](TODO)

# Context9 - Open Source, Real-Time MCP Doc Server for AI Agents

Bring Living Documentation into Your AI Context — Securely, Locally, and Under Your Control

[![Apache 2.0 licensed](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

[![简体中文](https://img.shields.io/badge/docs-简体中文-orange)](./docs/README.zh-CN.md)
[![繁體中文](https://img.shields.io/badge/docs-繁體中文-darkorange)](./docs/README.zh-TW.md)
[![日本語](https://img.shields.io/badge/docs-日本語-red)](./docs/README.ja.md)
[![한국어 문서](https://img.shields.io/badge/docs-한국어-darkred)](./docs/README.ko.md)
[![Documentación en Español](https://img.shields.io/badge/docs-Español-blue)](./docs/README.es.md)
[![Documentation en Français](https://img.shields.io/badge/docs-Français-royalblue)](./docs/README.fr.md)
[![Documentação em Português (Brasil)](https://img.shields.io/badge/docs-Português%20(Brasil)-purple)](./docs/README.pt-BR.md)
[![Documentazione in italiano](https://img.shields.io/badge/docs-Italian-indigo)](./docs/README.it.md)
[![Dokumentation auf Deutsch](https://img.shields.io/badge/docs-Deutsch-darkgreen)](./docs/README.de.md)
[![Документация на русском языке](https://img.shields.io/badge/docs-Русский-navy)](./docs/README.ru.md)
[![Українська документація](https://img.shields.io/badge/docs-Українська-steelblue)](./docs/README.uk.md)
[![Türkçe Doküman](https://img.shields.io/badge/docs-Türkçe-teal)](./docs/README.tr.md)
[![Dokumentasi Bahasa Indonesia](https://img.shields.io/badge/docs-Bahasa%20Indonesia-cadetblue)](./docs/README.id-ID.md)
[![Arabic Documentation](https://img.shields.io/badge/docs-Arabic-black)](./docs/README.ar.md)
[![Tiếng Việt](https://img.shields.io/badge/docs-Tiếng%20Việt-darkcyan)](./docs/README.vi.md)

---

## What makes Context9 unique

<table>
<tr>
<td width="50%" valign="top" align="center">
<h3>❌ Without Context9</h3>
<div align="left">
<ul>
  <li>❌ Relies on outdated code documentation and examples</li>
  <li>❌ Private team knowledge risks leakage through public MCP infrastructure</li>
  <li>❌ Constant document syncing introduces significant cost and friction</li>
  <li>❌ No access to private or internal documentation</li>
</ul>
</div>
</td>

<td width="50%" valign="top" align="center">
<h3>✅ With Context9</h3>
<div align="left">
<ul>
  <li>✅ Always operates on up-to-date code documentation and examples</li>
  <li>✅ Deployed within the team to keep documentation secure and private</li>
  <li>✅ Seamless document management designed for agile development, transparent to users</li>
  <li>✅ Unified access to live documentation across private and public sources</li>
</ul>
</div>
</td>
</tr>

<tr>
<td width="50%" valign="top" align="center">
<h3>🔒 It runs locally</h3>
<div align="left">
<ul>
  <li>Your code and docs never leave your infrastructure</li>
  <li>Deployed inside your team’s network or on personal machines</li>
  <li>No external dependency or cloud latency in the documentation loop</li>
</ul>
</div>
</td>

<td width="50%" valign="top" align="center">
<h3>🎯 It keeps agents focused</h3>
<div align="left">
<ul>
  <li>Light-weight, only relevant repositories are included in context</li>
  <li>No global crawling or searching across massive codebases</li>
  <li>Reduced context window size, fewer hallucinations</li>
</ul>
</div>
</td>
</tr>
</table>


## What Context9 Actually Does

🚀 **Context9 (Context Mine)** is an MCP (Model Context Protocol) server designed for modern development teams, enabling AI assistants and code agents to securely and timely access documentation while maintaining full privacy control.

<table>
  <tr>
    <td width="33%" valign="top">
      <h3>📚 Live Docs</h3>
      <div>
        <p>Always reads the latest docs from real repos</p>
        <p>No stale examples</p>
      </div>
    </td>
    <td width="33%" valign="top">
      <h3>🔐 Local &amp; Private</h3>
      <div>
        <p>Runs inside your own environment</p>
        <p>No public infrastructure</p>
      </div>
    </td>
    <td width="33%" valign="top">
      <h3>🧠 Focused Context</h3>
      <div>
        <p>Feeds agents only relevant information</p>
        <p>Less context, fewer hallucinations</p>
      </div>
    </td>
  </tr>

  <tr>
    <td width="33%" valign="top">
      <h3>🎯 Scoped Access</h3>
      <div>
        <p>Only the repos you configure</p>
        <p>Private and public supported</p>
      </div>
    </td>
    <td width="33%" valign="top">
      <h3>🔌 MCP Native</h3>
      <div>
        <p>Works out of the box with MCP agents</p>
        <p>No plugins or hacks</p>
      </div>
    </td>
    <td width="33%" valign="top">
      <h3>🛠 You’re in Control</h3>
      <div>
        <p>Approve access, see logs, stop anytime</p>
        <p>Your infra, your rules</p>
      </div>
    </td>
  </tr>
</table>


Simply add `use context9` to your prompt, or let rules handle automatic invocation.

```text
With Context9, inspect the newly added frontend APIs in the team, implement the corresponding backend endpoints, and verify them with tests.
```

```text
Deploy the latest version of the backend server following the documentation with Context9.
```

## How to use it

| Step | Action | Details |
|:----:|--------|---------|
| **1** | **Deploy Context9** | Start Context9 MCP service on your own server, see [Deployment](#deployment) |
| **2** | **Integrate Context9 with Agent** | Bring living and secured documentation to your agent, see [Integrate](#integrate-context9-with-agent) |
| **3** | **Update Docs** | Enable agile development with up-to-date docs, see [Update](#work-with-context9) |

## Deployment

### Requirements

- Python >= 3.10
- Repository access (public or with authentication token)
- Optional: Webhook setup for event-based updates

### Deploy Context9 on server

#### Clone Context9 repository

```shell
git clone https://github.com/Prism-Shadow/context9.git && cd context9
```


#### Set up python environment

```shell
# Install the package
uv pip install -e .

# Or install with development dependencies
uv pip install -e .[dev]
```

#### Configure repository

Configure the repositories you need in `config.yaml` (private & public repositories)

An example of `config.yaml` file. [config example](config.yaml)
```yaml
# config.yaml
repos:
# Private Repo 1
  - owner: OwnerName
    repo: RepoName
    branch: BranchName
    root_spec_path: RootSpecPath
# Private Repo 2
  - owner: OwnerName
    repo: RepoName
    branch: BranchName
# Public Repo 1 (Example: sglang)
  - owner: sgl-project
    repo: sglang
    branch: main
    root_spec_path: README.md
```

You can include both private and public repositories.

<details>
<summary><b>Configure public repos</b></summary>
Simply specify the repository owner, name, and branch in <code>config.yaml</code>.
</details>

<details>
<summary><b>Configure private repos</b></summary>
1. Specify the repository owner, name, and branch in <code>config.yaml</code>.
2. Add an authentication token with repository access permissions to your environment. [Configure environment](#configure-environment)
</details>

#### Configure Environment

Set the following environment variables (create a `.env` file or export them directly):
* `CTX9_API_KEY` (Required): API key used for server authentication to access private resources. **Specified by an administrator. Keep it random and confidential.**
* `GITHUB_TOKEN` (Optional): Required when configuring private repositories in `config.yaml`. This is not limited to a GitHub personal access token—any organization-issued repository access token is supported, as long as it conforms to the GitHub API specification.

An example of `.env` file. [.env example](.env_example)

```env
GITHUB_TOKEN=github_token
CTX9_API_KEY=XXXXXXXXXXXXXXXX
```

#### Launch the Context9 server

```shell
# Default:
# Sync repos every 600 seconds (10 minutes)
# Run server on port 8011
uv run python -m context9.server --config_file config.yaml

# Sync repos every 60 seconds (1 minute)
uv run python -m context9.server --github_sync_interval 60 --config_file config.yaml

# Run server on port 8080
uv run python -m context9.server --config_file config.yaml --port 8080
```

You can also run Context9 using Docker. Context9 provides a ready-to-use [Dockerfile](Dockerfile).


## Integrate Context9 with Agent
After deploying the Context9 service, you can seamlessly integrate both private and public real-time code documentation into your agents. You can connect to the Context9 MCP service using tools such as Cursor and Claude Code.

<details>
<summary><b>Install in Cursor</b></summary>
Go to: <code>Settings</code> -> <code>Cursor Settings</code> -> <code>Tools & MCP</code> -> <code>Add a Custom MCP Server</code>

Paste the configuration below into `~/.cursor/mcp.json`. If you want to configure Context9 for a specific project only, create `.cursor/mcp.json` in the project directory and paste the configuration there.

```json
{
  "mcpServers": {
    "Context9": {
      "url": "<Context9_url>:8011/api/mcp/",
      "headers": {
        "Authorization": "Bearer <CTX9_API_KEY in .env>"
      }
    }
  }
}
```
</details>

<details>
<summary><b>Install in Claude Code</b></summary>
Run the following command to add Context9 to Claude Code.

```shell
claude mcp add --transport http Context9 <Context9_url>:8011/api/mcp/ --header "Authorization: Bearer <CTX9_API_KEY in .env>"
```
</details>

## Work with Context9


<details>
<summary><b>1. Set up entry documentation</b></summary>
To enable Context9 to correctly discover and index your repository documentation, each repository should provide a Spec document.
By default, Context9 expects a file named spec.md at the root of the repository.
```text
your-repo/
├── spec.md          ← Specification entry point
├── README.md
├── docs/
│   └── ...
└── ...
```
> If you need to use a different filename or path, coordinate with the Context9 administrator to update the repository configuration.

</details>

<details>
<summary><b>2. Use relative link of other doc</b></summary>

You do not need to think about MCP, indexing, or document resolution. Just maintain documentation links using normal repository-relative paths, exactly as you would for human readers.

Example in documentation.

```markdown
## Related Documents
- [Detailed Guide](docs/detailed-guide.md)
- [API Reference](guides/api-reference.md)
- [FAQ](faq.md)
```

As long as these links are valid within the repository, Context9 will:

- Discover the documents
- Index them correctly
- Make them available to AI agents in real time

</details>



<br />

<div align="center">

**[Website](TODO)** · **[X](TODO)** · **[Discord](TODO)** · **[Issues](TODO)**

</div>


## ⭐ Star History
[![Star History Chart](https://api.star-history.com/svg?repos=Prism-Shadow/context9&type=Date)](https://www.star-history.com/#Prism-Shadow/context9&Date)




