![Cover](TODO)

# Context9 - Secure Real-Time Docs for LLM & Code Agents

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

## About

### ❌ Without Context9

- ❌ Relies on outdated code documentation and examples
- ❌ Private team knowledge risks leakage through public MCP infrastructure
- ❌ Constant document syncing introduces significant cost and friction
- ❌ No access to private or internal documentation

### ✅ With Context9

- ✅ Always operates on up-to-date code documentation and examples
- ✅ Deployed within the team to keep documentation secure and private
- ✅ Seamless document management designed for agile development, transparent to users
- ✅ Unified access to live documentation across private and public sources


🚀 **Context9 (Context Mine)** is an MCP (Model Context Protocol) server designed for modern development teams, enabling AI assistants and code agents to securely and timely access documentation while maintaining full privacy control.

Simply add `use context9` to your prompt, or let rules handle automatic invocation.

```text
With Context9, inspect the newly added frontend APIs in the team, implement the corresponding backend endpoints, and verify them with tests.
```

```text
Deploy the latest version of the backend server following the documentation with Context9.
```

Documentation Guide

- To deploy Context9 for your team or personal use, see [Deployment](#deployment).
- If you already have a Context9 service running and want to connect it to Cursor or Claude Code, see [Integrate Context9 with Your Agent](#integrate-context9-with-your-agent).

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
  - owner: OwnerName                # 
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



## Connect with Us

Stay updated and join our community:

- Follow us on [X](TODO) for the latest news and updates
- Visit our [Website](TODO)
- Join our [Discord](TODO)


## ⭐ Star History
[![Star History Chart](https://api.star-history.com/svg?repos=Prism-Shadow/context9&type=Date)](https://www.star-history.com/#Prism-Shadow/context9&Date)




