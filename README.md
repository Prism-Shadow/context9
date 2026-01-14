# Context9

An MCP (Model Context Protocol) server for reading documents from multiple GitHub repositories. Context9 provides a simple and efficient way to access documentation and files from GitHub repositories through the MCP protocol.

## Features

- **Multi-Repository Support**: Manage and access documents from multiple GitHub repositories
- **GitHub Integration**: Read files directly from GitHub repositories using the GitHub REST API
- **Local Caching**: Efficient local caching with periodic synchronization to reduce API calls
- **Multiple Update Modes**: 
  - Polling-based updates with configurable sync intervals
  - Event-based updates via GitHub webhooks
- **MCP Protocol**: Full support for the Model Context Protocol standard
- **API Authentication**: Bearer token authentication for secure access
- **Simple URL Format**: Use `remotedoc://owner/repo/branch/path` URLs to reference files in your repositories
- **Document Discovery**: Automatically discover available repositories and their documentation
- **Automatic Path Rewriting**: Automatically rewrites relative paths in Markdown files to `remotedoc://` URLs for proper cross-referencing

## Requirements

- Python >= 3.10
- GitHub repository access (public or with authentication token)
- Optional: GitHub webhook setup for event-based updates

## Installation

### Using uv (Recommended)

```bash
# Install the package
uv pip install -e .

# Or install with development dependencies
uv pip install -e .[dev]
```

### Using pip

```bash
pip install -e .
```

## Configuration

Context9 uses a YAML configuration file to manage multiple repositories. Create a `config.yaml` file in your project root:

### Configuration File Format

Create a `config.yaml` file with the following structure:

```yaml
repos:
  - owner: OwnerName
    repo: RepoName
    branch: BranchName
    root_spec_path: RootSpecPath
  - owner: OwnerName
    repo: RepoName
    branch: BranchName
  - owner: OwnerName
    repo: RepoName
    branch: BranchName
    root_spec_path: RootSpecPath
```

**Configuration Fields:**
- `owner` (required): GitHub repository owner (username or organization)
- `repo` (required): Repository name
- `branch` (required): Branch name to sync
- `root_spec_path` (optional): Path to the root specification file, defaults to `spec.md` if not specified

**Note:** You can see a complete example in `config_example.yaml`. Copy it to `config.yaml` and customize it with your repository information.

### Environment Variables

Set the following environment variables (create a `.env` file or export them):

#### Required Configuration

- `CTX9_API_KEY`: API key for server authentication (required)

#### Optional Configuration

- `GITHUB_TOKEN`: GitHub personal access token (recommended for higher rate limits and private repositories)
- `MCP_SERVER_NAME`: Custom server name (default: "Context9")
- `MCP_SERVER_DESCRIPTION`: Custom server description

### Example `.env` file

```env
GITHUB_TOKEN=ghp_your_token_here
CTX9_API_KEY=your-api-key-here
```

## Usage

### Starting the Server

Context9 supports two modes of operation:

#### Polling-Based Updates (Default)

Synchronizes repositories at regular intervals:

```bash
# Sync every 60 seconds
uv run python -m context9.server --github_sync_interval 60 --config_file config.yaml

# Sync every 600 seconds
uv run python -m context9.server --github_sync_interval 600 --config_file config.yaml
```

**Note:** You must specify either `--github_sync_interval` or `--enable_github_webhook` (they are mutually exclusive).

#### Event-Based Updates (GitHub Webhook)

Uses GitHub webhooks for real-time updates:

```bash
uv run python -m context9.server --enable_github_webhook --config_file config.yaml
```

**Note:** When using webhook mode, `--github_sync_interval` cannot be used.

The server will start on `http://0.0.0.0:8011` with the MCP endpoint at `/api/mcp/`.

### GitHub Webhook Setup

If using webhook mode, configure GitHub webhooks for each repository:

1. Go to your repository settings → Webhooks
2. Add a new webhook
3. Set the Payload URL to: `http://your-server:8011/api/github`
4. Set Content type to: `application/json`
5. Select events: `push` (and optionally `repository` for branch changes)
6. Save the webhook

Repeat for each repository you want to monitor.

### Using the MCP Tools

Once the server is running, you can use the following tools:

#### Tool: `get_doc_list`

Get a list of all available repositories and their documentation.

**Parameters:**
- None

**Returns:**
- A list of dictionaries, each containing:
  - `repo_name`: The name of the repository
  - `repo_description`: The description of the repository (fetched from GitHub)
  - `repo_spec_path`: The path to the root specification file in `remotedoc://` format

**Example Usage:**

```python
# In an MCP client
result = await client.call_tool("get_doc_list", {})
print(result)
# Output: [
#   {
#     "repo_name": "RepoName",
#     "repo_description": "Repository description from GitHub",
#     "repo_spec_path": "remotedoc://OwnerName/RepoName/BranchName/RootSpecPath"
#   },
#   ...
# ]
```

#### Tool: `read_doc`

Reads a document from GitHub using a `remotedoc://` URL.

**Parameters:**
- `url` (string): A `remotedoc://` URL pointing to the document
  - Format: `remotedoc://owner/repo/branch/path/to/file.md`
  - Examples:
    - `remotedoc://OwnerName/RepoName/BranchName/API.md`
    - `remotedoc://OwnerName/RepoName/BranchName/docs/guide.md`
    - `remotedoc://OwnerName/RepoName/BranchName/docs/api/spec.md`

**Returns:**
- The content of the document as a string (with relative paths rewritten to `remotedoc://` URLs)

**Example Usage:**

```python
# In an MCP client
result = await client.call_tool("read_doc", {
    "url": "remotedoc://OwnerName/RepoName/BranchName/API.md"
})
print(result)
```

**Note:** The URL format includes the repository owner, repository name, and branch to uniquely identify the file. Relative paths in Markdown files are automatically rewritten to `remotedoc://` URLs for proper cross-referencing.

### API Authentication

All requests must include the API key using the **Authorization header with Bearer token format**:

- **HTTP Header**: `Authorization: Bearer your-api-key`

**Example:**
```bash
curl -H "Authorization: Bearer your-api-key" http://localhost:8011/api/mcp/
```

**Note:** 
- The API key is required and must be set via the `CTX9_API_KEY` environment variable
- The GitHub webhook endpoint (`/api/github`) does not require API key authentication as it uses GitHub's signature verification
- The Authorization header is case-insensitive, but the Bearer token format is required

## Docker Deployment

### Prerequisites

- Docker 20.10+
- At least 512MB available memory
- At least 1GB available disk space

### Quick Start

#### 1. Prepare Environment Variables

Create a `.env` file with the following content:

```env
# Required
CTX9_API_KEY=your_secure_api_key_here

# Optional but recommended
GITHUB_TOKEN=your_github_personal_access_token
MCP_SERVER_NAME=Context9
MCP_SERVER_DESCRIPTION=MCP server for reading docs from GitHub
```

**Important Notes:**
- `GITHUB_TOKEN` is used to increase GitHub API rate limits. It's recommended to create a GitHub Personal Access Token.
- `CTX9_API_KEY` is required for API authentication. Clients need to include `Authorization: Bearer <your_api_key>` in request headers.

#### 2. Prepare Configuration File

Ensure you have a `config.yaml` file in your project root (see [Configuration](#configuration) section). The `config.yaml` file will be copied into the Docker image during the build process.

#### 3. Build Docker Image

```bash
docker build -t context9:latest .
```

#### 4. Run Container

Context9 supports two synchronization modes:

##### Polling Mode (Default)

Synchronizes repositories at regular intervals:

```bash
# Default sync interval (600 seconds)
docker run -d \
  --name context9-server \
  -p 8011:8011 \
  --env-file .env \
  --restart unless-stopped \
  context9:latest \
  python -m context9.server --github_sync_interval 600 --config_file config.yaml

# Custom sync interval (e.g., 60 seconds)
docker run -d \
  --name context9-server \
  -p 8011:8011 \
  --env-file .env \
  --restart unless-stopped \
  context9:latest \
  python -m context9.server --github_sync_interval 60 --config_file config.yaml
```

##### Webhook Mode (Recommended for Production)

Uses GitHub webhooks for real-time updates:

```bash
docker run -d \
  --name context9-server \
  -p 8011:8011 \
  --env-file .env \
  --restart unless-stopped \
  context9:latest \
  python -m context9.server --enable_github_webhook --config_file config.yaml
```

**Webhook Setup Steps:**

1. Go to your repository settings → Webhooks
2. Add a new webhook
3. Set Payload URL to: `https://your-domain.com/api/github`
4. Set Content type to: `application/json`
5. Select events: `Push` (and optionally `repository` for branch changes)
6. Save the webhook

Repeat for each repository you want to monitor.

### Verify Deployment

#### Check Service Status

```bash
docker ps | grep context9
```

#### Test Health Check

```bash
curl http://localhost:8011/api/mcp/
```

#### View Logs

```bash
docker logs -f context9-server
```

### Troubleshooting

#### Container Won't Start

1. Check if environment variables are set correctly:
   ```bash
   docker inspect context9-server | grep -A 20 Env
   ```

2. View container logs:
   ```bash
   docker logs context9-server
   ```

3. Verify GitHub configuration:
   - Ensure `config.yaml` is correct
   - Verify `GITHUB_TOKEN` is valid and has appropriate permissions

4. Check container status:
   ```bash
   docker ps -a | grep context9
   ```

#### API Requests Return 401/403

- Check if `CTX9_API_KEY` is set
- Ensure request headers contain the correct `Authorization: Bearer <token>` format
- Verify the API key matches the value in `CTX9_API_KEY` environment variable

#### Webhook Not Working

1. Check if GitHub webhook configuration is correct
2. Verify server is accessible from the internet
3. View webhook requests in container logs:
   ```bash
   docker logs context9-server | grep webhook
   ```

#### Container Keeps Restarting

1. Check container exit code:
   ```bash
   docker inspect context9-server | grep ExitCode
   ```

2. View full logs:
   ```bash
   docker logs --tail 100 context9-server
   ```

### Update Deployment

```bash
# Stop and remove old container
docker stop context9-server
docker rm context9-server

# Pull latest code (if building from Git)
git pull

# Rebuild image
docker build -t context9:latest .

# Start new container (choose mode based on your needs)
# Polling mode
docker run -d \
  --name context9-server \
  -p 8011:8011 \
  --env-file .env \
  --restart unless-stopped \
  context9:latest \
  python -m context9.server --github_sync_interval 600 --config_file config.yaml

# Or webhook mode
docker run -d \
  --name context9-server \
  -p 8011:8011 \
  --env-file .env \
  --restart unless-stopped \
  context9:latest \
  python -m context9.server --enable_github_webhook --config_file config.yaml
```

### Uninstall

```bash
# Stop and remove container
docker stop context9-server
docker rm context9-server

# Remove image (optional)
docker rmi context9:latest
```

## Development

### Setup Development Environment

```bash
# Install with development dependencies
uv pip install -e .[dev]

# Install pre-commit hooks
uv run pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest -vvv tests

# Or using Make
make test
```

### Code Quality

```bash
# Check code quality
make quality

# Auto-fix code style issues
make style

# Run pre-commit checks
make commit
```

## How It Works

1. **Configuration**: Context9 reads repository configuration from `config.yaml` file
2. **Multi-Repository Management**: Initializes GitHub clients for each configured repository
3. **Local Caching**: Each repository is cloned locally to `.github_cache/` directory for fast access
4. **Synchronization**: Repositories are synchronized periodically (polling) or via webhooks
5. **MCP Server**: Exposes `get_doc_list` and `read_doc` tools through the MCP protocol
6. **URL Parsing**: Parses `remotedoc://owner/repo/branch/path` URLs to extract repository and file information
7. **File Reading**: Fetches files from local cache and returns content
8. **Path Rewriting**: Automatically rewrites relative paths in Markdown files to `remotedoc://` URLs for proper cross-referencing

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ HTTP/JSON-RPC
                     │
┌────────────────────▼────────────────────────────────────┐
│              Context9 MCP Server                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  FastMCP Server (Port 8011)                      │  │
│  │  - get_doc_list()                                │  │
│  │  - read_doc(url)                                 │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  GitHub Client Manager                           │  │
│  │  - Multi-repository support                      │  │
│  │  - Local caching (.github_cache/)               │  │
│  │  - Sync management (polling/webhook)             │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ GitHub API / Git Clone
                     │
┌────────────────────▼────────────────────────────────────┐
│              GitHub Repositories                        │
│  - Repository 1 (owner/repo1)                          │
│  - Repository 2 (owner/repo2)                          │
│  - Repository 3 (owner/repo3)                          │
└─────────────────────────────────────────────────────────┘
```

## Error Handling

Context9 handles various error scenarios:

- **Invalid URL Format**: Returns a clear error message for malformed `remotedoc://` URLs (must be `remotedoc://owner/repo/branch/path`)
- **File Not Found**: Handles missing files gracefully with clear error messages
- **Rate Limiting**: Respects GitHub API rate limits (higher limits with authentication token)
- **Authentication Errors**: Provides clear feedback for authentication failures (401/403 with detailed messages)
- **Network Errors**: Implements retry logic for transient network issues
- **Configuration Errors**: Validates configuration file and provides helpful error messages
- **Path Traversal Protection**: Validates file paths to prevent directory traversal attacks

## Examples

See the `examples/` directory for usage examples:

- `basic_usage.py`: Basic usage examples
- `client_discovery_example.py`: MCP client discovery and tool usage examples

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.