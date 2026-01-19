from loguru import logger
from .mcp_instance import context9_mcp


@context9_mcp.tool()
def list_doc() -> list[dict[str, str]]:
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

    logger.info("Listing documentation...")

    return github_client.get_doc_list()
