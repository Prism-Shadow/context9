from ..client import GitHubClientError, GitHubFileNotFoundError
from ..utils import parse_remotedoc_url, URLParseError
from fastmcp.server.dependencies import get_http_headers

from .mcp_instance import context9_mcp
from loguru import logger

from .. import mcp_server


@context9_mcp.tool()
async def read_doc(url: str) -> str:
    """
    Read a document from GitHub using a remotedoc:// URL.

    This tool allows you to read Markdown files from a configured GitHub repository
    using a special remotedoc:// URL format. The URL should point to a file path
    relative to the repository root.

    Args:
        url: A remotedoc:// URL pointing to the document, e.g.,
             "remotedoc://spec.md" or "remotedoc://docs/gemini/spec.md"

    Returns:
        The content of the document as a string

    Raises:
        ValueError: If the URL is invalid or the file cannot be read
    """
    # remotedoc://owner/repo/branch/url

    headers = get_http_headers()
    api_key = headers.get("Authorization") or headers.get("authorization")
    if api_key and api_key.lower().startswith("bearer "):
        api_key = api_key[7:].strip()

    if not mcp_server.github_client:
        raise ValueError("Server not initialized. Please check configuration.")

    try:
        # Parse the URL
        logger.info(f"Parsing URL: {url}")
        file_path = parse_remotedoc_url(url)
        logger.info(f"Resolved file path: {file_path}")

        # Read file from GitHub
        content = mcp_server.github_client.read_doc(file_path, api_key)

        logger.info(
            f"Successfully read document: {file_path} ({len(content)} characters)"
        )
        return content

    except URLParseError as e:
        error_msg = f"Invalid URL format: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    except GitHubFileNotFoundError as e:
        error_msg = f"Document not found: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    except GitHubClientError as e:
        error_msg = f"Failed to read document: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error while reading document: {e}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg)
