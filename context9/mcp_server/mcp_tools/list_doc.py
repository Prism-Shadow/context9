from loguru import logger
from .mcp_instance import context9_mcp
from fastmcp.server.dependencies import get_http_headers
from .. import mcp_server


@context9_mcp.tool()
async def list_doc() -> list[dict[str, str]]:
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

    headers = get_http_headers()
    api_key = headers.get("Authorization") or headers.get("authorization")
    if api_key and api_key.lower().startswith("bearer "):
        api_key = api_key[7:].strip()

    logger.debug(f"API key: {api_key}")

    if not mcp_server.github_client:
        raise ValueError("Server not initialized. Please check configuration.")

    logger.debug("Listing documentation...")

    return mcp_server.github_client.list_doc(api_key)
