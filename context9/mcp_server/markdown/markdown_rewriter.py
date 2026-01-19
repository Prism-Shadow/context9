"""
Markdown Rewriter for converting relative paths to remotedoc:// URLs.

This module handles rewriting markdown content to convert relative file references
to remotedoc:// URLs.
"""

import re
from pathlib import Path


def rewrite_relative_paths(
    content: str,
    owner: str,
    repo: str,
    branch: str,
    current_path: str,
) -> str:
    """
    Rewrite relative file paths in markdown content to remotedoc:// URLs.

    This function processes markdown content and converts all relative file path
    references to remotedoc:// URLs in the format:
    remotedoc://owner/repo/branch/absolute_path

    Args:
        content: Markdown content to process
        owner: Repository owner name
        repo: Repository name
        branch: Branch name
        current_path: Current file path relative to repository root (used for resolving relative paths)

    Returns:
        Markdown content with relative paths converted to remotedoc:// URLs

    Examples:
        >>> content = "[Link](docs/spec.md)"
        >>> rewrite_relative_paths(content, "owner", "repo", "main", "README.md")
        '[Link](remotedoc://owner/repo/main/docs/spec.md)'

        >>> content = "![Image](./images/logo.png)"
        >>> rewrite_relative_paths(content, "owner", "repo", "main", "docs/guide.md")
        '![Image](remotedoc://owner/repo/main/docs/images/logo.png)'
    """
    if not content:
        return content

    # Normalize current_path: remove leading slash and ensure it's a valid path
    current_path = current_path.strip("/")
    if not current_path:
        current_path = "."

    # Get the directory of the current file (for resolving relative paths)
    current_dir = str(Path(current_path).parent) if current_path != "." else "."
    if current_dir == ".":
        current_dir = ""

    def is_absolute_url(path: str) -> bool:
        """Check if a path is an absolute URL (http, https, mailto, etc.)."""
        return bool(
            re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", path)
            or path.startswith("//")
            or path.startswith("mailto:")
        )

    def is_remotedoc_url(path: str) -> bool:
        """Check if a path is already a remotedoc:// URL."""
        return path.startswith("remotedoc://")

    def is_anchor_link(path: str) -> bool:
        """Check if a path is an anchor link (starts with #)."""
        return path.startswith("#")

    def resolve_relative_path(relative_path: str) -> str:
        """
        Resolve a relative path to an absolute path relative to repository root.

        Args:
            relative_path: Relative path from markdown

        Returns:
            Absolute path relative to repository root
        """
        # Skip if it's an anchor link (check before splitting)
        if is_anchor_link(relative_path):
            return relative_path

        # Remove query string and fragment if present
        path_part = relative_path.split("?")[0].split("#")[0]

        # Skip if it's already a URL or remotedoc URL
        if is_absolute_url(path_part) or is_remotedoc_url(path_part):
            return relative_path

        # Handle relative paths
        if current_dir:
            # Join current directory with relative path
            absolute_path = str(Path(current_dir) / path_part)
        else:
            absolute_path = path_part

        # Normalize the path (remove . and .. components)
        parts = []
        for part in absolute_path.split("/"):
            if part == ".":
                continue
            elif part == "..":
                if parts:
                    parts.pop()
            elif part:
                parts.append(part)

        normalized_path = "/".join(parts)

        # Preserve query string and fragment if they existed
        if "?" in relative_path or "#" in relative_path:
            separator = "?" if "?" in relative_path else "#"
            query_or_fragment = relative_path.split(separator, 1)[1]
            return f"{normalized_path}{separator}{query_or_fragment}"

        return normalized_path

    def convert_to_remotedoc(path: str) -> str:
        """
        Convert a file path to remotedoc:// URL format.

        Args:
            path: File path (may include query string or fragment)

        Returns:
            remotedoc:// URL or original path if it shouldn't be converted
        """
        # Check if it's an anchor link first (before splitting)
        if is_anchor_link(path):
            return path

        # Extract path part (before query string or fragment)
        path_part = path.split("?")[0].split("#")[0]

        # Don't convert if it's already a URL or remotedoc URL
        if is_absolute_url(path_part) or is_remotedoc_url(path_part):
            return path

        # Resolve relative path to absolute path
        absolute_path = resolve_relative_path(path)

        # If resolve_relative_path returned the original (because it's an anchor or URL),
        # return it as is
        if absolute_path == path and (
            is_anchor_link(path_part)
            or is_absolute_url(path_part)
            or is_remotedoc_url(path_part)
        ):
            return path

        # Check if absolute_path already contains fragment or query string
        # (resolve_relative_path may have already preserved them)
        if "?" in absolute_path or "#" in absolute_path:
            # absolute_path already contains fragment/query, use it directly
            return f"remotedoc://{owner}/{repo}/{branch}/{absolute_path}"

        # Build remotedoc:// URL
        remotedoc_url = f"remotedoc://{owner}/{repo}/{branch}/{absolute_path}"

        # Preserve query string and fragment from original path if they weren't already included
        if "?" in path or "#" in path:
            separator = "?" if "?" in path else "#"
            query_or_fragment = path.split(separator, 1)[1]
            return f"{remotedoc_url}{separator}{query_or_fragment}"

        return remotedoc_url

    # Pattern for inline links: [text](path) or [text](path "title")
    # Matches: [text](path) or [text](path "title") or [text](path 'title')
    inline_link_pattern = re.compile(
        r"\[([^\]]*)\]\(([^)]+)\)", re.MULTILINE | re.DOTALL
    )

    def replace_inline_link(match: re.Match) -> str:
        """Replace inline link path with remotedoc:// URL."""
        text = match.group(1)
        path_with_title = match.group(2)

        # Extract path (before title if present)
        # Title can be in quotes: "title" or 'title'
        path_match = re.match(
            r'^([^\s"\'<>]+)(?:\s+["\']([^"\']*)["\'])?$', path_with_title
        )
        if path_match:
            path = path_match.group(1)
            title = path_match.group(2)
            converted_path = convert_to_remotedoc(path)
            if title:
                return f'[{text}]({converted_path} "{title}")'
            else:
                return f"[{text}]({converted_path})"
        else:
            # Fallback: treat entire match as path
            converted_path = convert_to_remotedoc(path_with_title)
            return f"[{text}]({converted_path})"

    # Pattern for reference link definitions: [ref]: path "title" (optional)
    # Matches: [ref]: path or [ref]: path "title" or [ref]: path 'title'
    reference_link_pattern = re.compile(
        r'^(\s*)\[([^\]]+)\]:\s+([^\s"\']+)(?:\s+["\']([^"\']*)["\'])?\s*$',
        re.MULTILINE,
    )

    def replace_reference_link(match: re.Match) -> str:
        """Replace reference link definition path with remotedoc:// URL."""
        indent = match.group(1)
        ref = match.group(2)
        path = match.group(3)
        title = match.group(4)

        converted_path = convert_to_remotedoc(path)
        if title:
            return f'{indent}[{ref}]: {converted_path} "{title}"'
        else:
            return f"{indent}[{ref}]: {converted_path}"

    # Apply replacements
    content = inline_link_pattern.sub(replace_inline_link, content)
    content = reference_link_pattern.sub(replace_reference_link, content)

    return content
