![Cover](public/context9.png)

# Context9 - Sync your knowledge to a live, agent-ready local MCP server

<div align="center">
  <h2>Bring Living Knowledge into Your AI Context</h2>
  <p><b>Secure</b> &middot; <b>Open-source</b> &middot; <b>Fully Under Your Control</b></p>
</div>

<div align="center">

**[Website](TODO)** · **[X](TODO)** · **[Discord](TODO)** · **[Issues](TODO)**

</div>

<div align="center">

[![Apache 2.0 licensed](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
![MCP](https://img.shields.io/badge/MCP-Native-brightgreen)

</div>

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
  <li>❌ Uses outdated docs and examples</li>
  <li>❌ Private knowledge is hard to access and easy to leak</li>
</ul>
</div>
</td>

<td width="50%" valign="top" align="center">
<h3>✅ With Context9</h3>
<div align="left">
<ul>
  <li>✅ Always uses the latest docs from real repos</li>
  <li>✅ Secure access to both private and public docs</li>
</ul>
</div>
</td>
</tr>

<tr>
<td width="50%" valign="top" align="center">
<h3>🔒 It runs locally</h3>
<div align="left">
<ul>
  <li>Your code and docs stay inside your server</li>
  <li>No cloud dependency or extra sync overhead</li>
</ul>
</div>
</td>

<td width="50%" valign="top" align="center">
<h3>🎯 It keeps agents focused</h3>
<div align="left">
<ul>
  <li>Only relevant repositories are included in context</li>
  <li>Smaller context, fewer hallucinations</li>
</ul>
</div>
</td>
</tr>
</table>

## 🚀 What Context9 Actually Does

**Context9 (Context Mine)** is an MCP (Model Context Protocol) server designed for modern development teams, enabling AI assistants and code agents to securely and timely access documentation while maintaining full privacy control. 

Context9 provides an easy-to-use graphical user interface (GUI) that includes a complete MCP workflow, MCP testing, and access control, enabling deployment in large teams for multi-project collaboration.

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


Context9 provides two deployment methods, CLI and GUI. GUI method provide a no-code way to configure repositories and API keys. 

- CLI method: Suitable for individual users or teams that do not need to frequently change repository configurations
- GUI method: Suitable for large team deployments that require complex permission control and frequent repository configuration changes

### Use Context9 in CLI

| Step | Action | Details |
|:----:|--------|---------|
| **1** | **Deploy Context9 CLI** | Start Context9 MCP service on your own server, see [CLI Deployment](#cli-deployment) |
| **2** | **Integrate Context9 with Agent** | Connect Cursor / Claude Code, see [Integrate](#integrate-context9-with-agent) |
| **3** | **Update Docs** | Let agents work with Context9, see [Update](#work-with-context9) |

### Use Context9 in GUI

| Step | Action | Details |
|:----:|--------|---------|
| **1** | **Deploy Context9 GUI** | Start Context9 MCP service and GUI on your own server, see [GUI Deployment](#gui-deployment) |
| **2** | **Integrate Context9 with Agent** | Connect Cursor / Claude Code, see [Integrate](#integrate-context9-with-agent) |
| **3** | **Update Docs** | Let agents work with Context9, see [Update](#work-with-context9) |

## CLI Deployment

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
uv sync

# Or install with development dependencies
uv sync --dev
```

#### Configure repository

Configure the repositories you need in `config.yaml` (private & public repositories)

An example of `config.yaml` file. [config example](config_example.yaml)
```yaml
# config.yaml
repos:
# Private Repo 1
  - owner: OwnerName
    repo: RepoName
    branch: BranchName
    root_spec_path: RootSpecPath
# Private Repo 2 (Default root_spec_path is spec.md)
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

<ol>
  <li>
    Specify the repository owner, name, and branch in
    <code>config.yaml</code>.
  </li>
  <li>
    Add an authentication token with repository access permissions
    to your environment.
    <a href="#configure-environment">Configure environment</a>
  </li>
</ol>

</details>

#### Configure Environment

Set the following environment variables (create a `.env` file or export them directly):
* `CTX9_API_KEY` (Required): API key used for server authentication to access private resources. **Specified by an administrator. Keep it random and confidential.**
* `GITHUB_TOKEN` (Optional): Required when configuring private repositories in `config.yaml`. This is not limited to a GitHub personal access token—any organization-issued repository access token is supported, as long as it conforms to the GitHub API specification.
* `CONTEXT9_PORT` (Optional): Specifies the port number on which the Context9 MCP service runs. If not specified, it defaults to 8011.

An example of `.env` file. [.env example](.env_example)

```env
GITHUB_TOKEN=github_token
CTX9_API_KEY=XXXXXXXXXXXXXXXX

# Optional
CONTEXT9_PORT=8080
```

#### Launch Context9 server

```shell
# Default:
# Sync repos every 600 seconds (10 minutes)
# Run server on port 8011
uv run python -m context9.server --config_file config.yaml

# Sync repos every 60 seconds (1 minute)
uv run python -m context9.server --github_sync_interval 60 --config_file config.yaml

# Run server on port 8080 (or define CONTEXT9_PORT in .env)
CONTEXT9_PORT=8080 uv run python -m context9.server --config_file config.yaml
```

#### Launch Context9 Server with Docker

You can also run Context9 using Docker. Context9 provides a ready-to-use [Dockerfile](docker/Dockerfile-cli).

The `config.yaml` file is included in the Docker image during the build process, so there is no need to provide it again when starting the container.

```shell
# Build docker image
docker build -f docker/Dockerfile-cli -t context9:latest .

# Run docker container
# Change port mapping according to your .env
docker run -d \
    --name context9 \
    -p 8011:8011 \
    --env-file .env \
    --restart unless-stopped \
    context9:latest
```

## GUI Delopyment

### Requirements

- Python >= 3.10
- Node.js >= 18
- Repository access (public or with authentication token)

### Deploy Context9 GUI on server

#### Clone Context9 repository

```shell
git clone https://github.com/Prism-Shadow/context9.git && cd context9
```

#### Set up python environment

```shell
# Install the package
uv sync

# Or install with development dependencies
uv sync --dev
```

#### Install frontend dependencies

```shell
cd gui
npm install
cd ..
```

#### Configure Environment

Set the following environment variables (create a `.env` file, see [.env example](.env_example) or export them directly):

* `CONTEXT9_PORT` (Optional): Specifies the port number on which the Context9 service runs. Defaults to 8011.

```env
CONTEXT9_PORT=xxxx
```

#### Build GUI and launch server

```shell
# Build frontend and start backend (serves GUI + API on the same port)
# Server is running on port 8011, visit http://<Context9_url>:8011/
uv run python scripts/start.py --github_sync_interval 600

# Update repos every 60 seconds
uv run python scripts/start.py --github_sync_interval 60
```

Once started, open the GUI at: `http://<Context9_url>:8011/`

#### Launch Context9 GUI with Docker

You can also run the GUI deployment using Docker. Context9 provides a ready-to-use [Dockerfile](docker/Dockerfile-gui).

```shell
# Build docker image
docker build -f docker/Dockerfile-gui -t context9-gui:latest .

# Run docker container
docker run -d \
    --name context9-gui \
    -p 8011:8011 \
    --env-file .env \
    --restart unless-stopped \
    context9-gui:latest \
    python -m context9.server --github_sync_interval 600
```

The GUI and API are served from the same port. Open `http://<Context9_url>:8011/` in your browser.

The default login username is `ctx9-admin`, and the default password is `88888888`. Change passward when you login to Context9.

#### Add repositories and API keys

Context9-GUI provides a no-code way to configure repositories and API keys, and it can apply different access controls for different API keys. Please log in to the Context9 GUI to configure them.

#### Test the configured MCP services

Context9-GUI includes an MCP Inspector that lets users test each MCP service for an API key in place. In the Sidebar, enter the following in the MCP Inspector, connect to Context9, and run tool tests:

- Context9 URL
- API key

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
<pre><code>
your-repo/
├── spec.md          ← Specification entry point
├── README.md
├── docs/
│   └── ...
└── ...
</code></pre>

<blockquote>
If you need to use a different filename or path, coordinate with the Context9 administrator to update the repository configuration.
</blockquote>

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

## License

Licensed under the Apache License, version 2.0. See [LICENSE](LICENSE) for details.

## ⭐ Star History
[![Star History Chart](https://api.star-history.com/svg?repos=Prism-Shadow/context9&type=Date)](https://www.star-history.com/#Prism-Shadow/context9&Date)
