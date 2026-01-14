from .github_client import GitHubClientError, GitHubFileNotFoundError
from .url_parser import parse_remotedoc_url, URLParseError

from fastmcp import FastMCP

from loguru import logger

context9_mcp = FastMCP("Context9")


@context9_mcp.tool()
def read_doc(url: str) -> str:
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
    from .mcp_server import github_client

    if not github_client:
        raise ValueError("Server not initialized. Please check configuration.")

    try:
        # Parse the URL
        logger.info(f"Parsing URL: {url}")
        file_path = parse_remotedoc_url(url)
        logger.info(f"Resolved file path: {file_path}")

        # Read file from GitHub
        content = github_client.read_file(file_path)

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


@context9_mcp.tool()
def get_doc_list() -> list[dict[str, str]]:
    """
    Read documentation list managed by Context9.

    Context9 manages several repositories and their documentation files.
    This tool allows you to get all avaiable repo_name, repo_description and repo_spec_path.
    repo_name is the name of the repository.
    repo_description is the description of the repository.
    repo_spec_path is the path to the root specification file of the repository in the format of remotedoc://path/to/file.md.
    After getting the list, you can use the read_doc tool to read the documentation file.

    Args:
        None

    Returns:
        A list of dictionaries, each dictionary containing the repo_name, repo_description and repo_spec_path

    Raises:
        ValueError: If the documentation list cannot be read
        Exception: If an unexpected error occurs
    """
    from .mcp_server import github_client

    if not github_client:
        raise ValueError("Server not initialized. Please check configuration.")

    return github_client.get_doc_list()
