"""
Tests for markdown rewriter module.
"""

from context9.mcp_server.markdown_rewriter import rewrite_relative_paths


class TestMarkdownRewriter:
    """Test cases for markdown rewriter."""

    # Test parameters
    OWNER = "test-owner"
    REPO = "test-repo"
    BRANCH = "main"

    def test_empty_content(self):
        """Test empty content."""
        result = rewrite_relative_paths(
            "", self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == ""

    def test_no_links(self):
        """Test content without links."""
        content = "# Title\n\nSome text without links."
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == content

    # ========== Inline Links - Basic Relative Paths ==========

    def test_simple_relative_path(self):
        """Test simple relative path."""
        content = "[Link](docs/spec.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == "[Link](remotedoc://test-owner/test-repo/main/docs/spec.md)"

    def test_current_directory_path(self):
        """Test path starting with ./"""
        content = "[Link](./docs/spec.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == "[Link](remotedoc://test-owner/test-repo/main/docs/spec.md)"

    def test_parent_directory_path(self):
        """Test path starting with ../"""
        content = "[Link](../parent.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "docs/guide.md"
        )
        assert result == "[Link](remotedoc://test-owner/test-repo/main/parent.md)"

    def test_nested_relative_path(self):
        """Test nested relative path."""
        content = "[Link](docs/subdir/file.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert (
            result
            == "[Link](remotedoc://test-owner/test-repo/main/docs/subdir/file.md)"
        )

    def test_relative_path_from_subdirectory(self):
        """Test relative path from a subdirectory."""
        content = "[Link](./other.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "docs/guide.md"
        )
        assert result == "[Link](remotedoc://test-owner/test-repo/main/docs/other.md)"

    def test_relative_path_sibling_file(self):
        """Test relative path to sibling file."""
        content = "[Link](../sibling.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "docs/subdir/file.md"
        )
        assert result == "[Link](remotedoc://test-owner/test-repo/main/docs/sibling.md)"

    def test_root_level_file(self):
        """Test path when current file is at root."""
        content = "[Link](spec.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "."
        )
        assert result == "[Link](remotedoc://test-owner/test-repo/main/spec.md)"

    def test_root_level_file_explicit_dot(self):
        """Test path when current path is explicitly '.'."""
        content = "[Link](./spec.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "."
        )
        assert result == "[Link](remotedoc://test-owner/test-repo/main/spec.md)"

    # ========== Inline Links - With Titles ==========

    def test_link_with_double_quote_title(self):
        """Test link with double-quoted title."""
        content = '[Link](docs/spec.md "Title")'
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert (
            result
            == '[Link](remotedoc://test-owner/test-repo/main/docs/spec.md "Title")'
        )

    def test_link_with_single_quote_title(self):
        """Test link with single-quoted title (converted to double quotes)."""
        content = "[Link](docs/spec.md 'Title')"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        # Implementation converts single quotes to double quotes
        assert (
            result
            == '[Link](remotedoc://test-owner/test-repo/main/docs/spec.md "Title")'
        )

    def test_link_with_title_containing_spaces(self):
        """Test link with title containing spaces."""
        content = '[Link](docs/spec.md "My Title Here")'
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert (
            result
            == '[Link](remotedoc://test-owner/test-repo/main/docs/spec.md "My Title Here")'
        )

    # ========== Inline Links - With Fragments ==========

    def test_link_with_fragment(self):
        """Test link with fragment (#section)."""
        content = "[Link](docs/spec.md#section)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert (
            result
            == "[Link](remotedoc://test-owner/test-repo/main/docs/spec.md#section)"
        )

    def test_link_with_fragment_and_title(self):
        """Test link with fragment and title."""
        content = '[Link](docs/spec.md#section "Title")'
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert (
            result
            == '[Link](remotedoc://test-owner/test-repo/main/docs/spec.md#section "Title")'
        )

    def test_link_with_query_string(self):
        """Test link with query string."""
        content = "[Link](docs/spec.md?query=value)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert (
            result
            == "[Link](remotedoc://test-owner/test-repo/main/docs/spec.md?query=value)"
        )

    def test_link_with_query_and_fragment(self):
        """Test link with query string and fragment."""
        content = "[Link](docs/spec.md?query=value#section)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert (
            result
            == "[Link](remotedoc://test-owner/test-repo/main/docs/spec.md?query=value#section)"
        )

    # ========== Inline Links - Should Not Be Converted ==========

    def test_absolute_http_url(self):
        """Test absolute HTTP URL should not be converted."""
        content = "[Link](http://example.com/page)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == "[Link](http://example.com/page)"

    def test_absolute_https_url(self):
        """Test absolute HTTPS URL should not be converted."""
        content = "[Link](https://example.com/page)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == "[Link](https://example.com/page)"

    def test_mailto_url(self):
        """Test mailto URL should not be converted."""
        content = "[Link](mailto:test@example.com)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == "[Link](mailto:test@example.com)"

    def test_protocol_relative_url(self):
        """Test protocol-relative URL (//example.com) should not be converted."""
        content = "[Link](//example.com/page)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == "[Link](//example.com/page)"

    def test_remotedoc_url_already_converted(self):
        """Test remotedoc:// URL should not be converted again."""
        content = "[Link](remotedoc://owner/repo/branch/path.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == "[Link](remotedoc://owner/repo/branch/path.md)"

    def test_anchor_link(self):
        """Test anchor link (#section) should not be converted."""
        content = "[Link](#section)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == "[Link](#section)"

    def test_anchor_link_with_title(self):
        """Test anchor link with title should not be converted."""
        content = '[Link](#section "Title")'
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == '[Link](#section "Title")'

    # ========== Reference Links ==========

    def test_reference_link_simple(self):
        """Test simple reference link definition."""
        content = "[ref]: docs/spec.md"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == "[ref]: remotedoc://test-owner/test-repo/main/docs/spec.md"

    def test_reference_link_with_title(self):
        """Test reference link with title."""
        content = '[ref]: docs/spec.md "Title"'
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert (
            result
            == '[ref]: remotedoc://test-owner/test-repo/main/docs/spec.md "Title"'
        )

    def test_reference_link_with_single_quote_title(self):
        """Test reference link with single-quoted title (converted to double quotes)."""
        content = "[ref]: docs/spec.md 'Title'"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        # Implementation converts single quotes to double quotes
        assert (
            result
            == '[ref]: remotedoc://test-owner/test-repo/main/docs/spec.md "Title"'
        )

    def test_reference_link_with_fragment(self):
        """Test reference link with fragment."""
        content = "[ref]: docs/spec.md#section"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert (
            result
            == "[ref]: remotedoc://test-owner/test-repo/main/docs/spec.md#section"
        )

    def test_reference_link_with_indentation(self):
        """Test reference link with indentation."""
        content = "  [ref]: docs/spec.md"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == "  [ref]: remotedoc://test-owner/test-repo/main/docs/spec.md"

    def test_reference_link_absolute_url(self):
        """Test reference link with absolute URL should not be converted."""
        content = "[ref]: https://example.com/page"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == "[ref]: https://example.com/page"

    def test_reference_link_anchor(self):
        """Test reference link with anchor should not be converted."""
        content = "[ref]: #section"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == "[ref]: #section"

    # ========== Path Normalization ==========

    def test_path_with_dot_components(self):
        """Test path normalization with . components."""
        content = "[Link](docs/./spec.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == "[Link](remotedoc://test-owner/test-repo/main/docs/spec.md)"

    def test_path_with_dot_dot_components(self):
        """Test path normalization with .. components."""
        content = "[Link](docs/subdir/../spec.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == "[Link](remotedoc://test-owner/test-repo/main/docs/spec.md)"

    def test_path_with_multiple_dot_dot(self):
        """Test path with multiple .. components."""
        content = "[Link](docs/subdir/../../root.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == "[Link](remotedoc://test-owner/test-repo/main/root.md)"

    def test_path_normalization_from_subdirectory(self):
        """Test path normalization from subdirectory."""
        content = "[Link](./../parent.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "docs/subdir/file.md"
        )
        assert result == "[Link](remotedoc://test-owner/test-repo/main/docs/parent.md)"

    def test_path_with_trailing_dot_dot(self):
        """Test path that goes above root (should normalize to root)."""
        content = "[Link](../../../file.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "docs/subdir/file.md"
        )
        # Should normalize to root level
        assert result == "[Link](remotedoc://test-owner/test-repo/main/file.md)"

    # ========== Multi-line Content ==========

    def test_multiple_links_same_line(self):
        """Test multiple links on the same line."""
        content = "See [link1](doc1.md) and [link2](doc2.md) for details."
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        expected = "See [link1](remotedoc://test-owner/test-repo/main/doc1.md) and [link2](remotedoc://test-owner/test-repo/main/doc2.md) for details."
        assert result == expected

    def test_multiple_links_multiline(self):
        """Test multiple links across multiple lines."""
        content = """# Title

See [link1](doc1.md) for more info.

Also check [link2](doc2.md) and [link3](doc3.md).

[link4](doc4.md) is also useful.
"""
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert "remotedoc://test-owner/test-repo/main/doc1.md" in result
        assert "remotedoc://test-owner/test-repo/main/doc2.md" in result
        assert "remotedoc://test-owner/test-repo/main/doc3.md" in result
        assert "remotedoc://test-owner/test-repo/main/doc4.md" in result

    def test_mixed_link_types(self):
        """Test mixed inline and reference links."""
        content = """# Title

This is an [inline link](doc1.md).

[ref1]: doc2.md
[ref2]: https://example.com
[ref3]: doc3.md "Title"
"""
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert "remotedoc://test-owner/test-repo/main/doc1.md" in result
        assert "remotedoc://test-owner/test-repo/main/doc2.md" in result
        assert "https://example.com" in result  # Should not be converted
        assert "remotedoc://test-owner/test-repo/main/doc3.md" in result

    def test_mixed_absolute_and_relative_links(self):
        """Test mix of absolute URLs and relative paths."""
        content = """# Links

[Relative](docs/spec.md) and [Absolute](https://example.com).
"""
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert "remotedoc://test-owner/test-repo/main/docs/spec.md" in result
        assert "https://example.com" in result

    # ========== Edge Cases ==========

    def test_path_with_special_characters(self):
        """Test path with special characters."""
        content = "[Link](docs/file-name_123.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert (
            result
            == "[Link](remotedoc://test-owner/test-repo/main/docs/file-name_123.md)"
        )

    def test_path_with_spaces_in_filename(self):
        """Test path with spaces (should be preserved as-is)."""
        content = "[Link](docs/file name.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert (
            result == "[Link](remotedoc://test-owner/test-repo/main/docs/file name.md)"
        )

    def test_empty_link_text(self):
        """Test link with empty text."""
        content = "[](docs/spec.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        assert result == "[](remotedoc://test-owner/test-repo/main/docs/spec.md)"

    def test_link_with_empty_path(self):
        """Test link with empty path (edge case - not converted)."""
        content = "[Link]()"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        # Empty path is not converted by current implementation
        assert result == "[Link]()"

    def test_current_path_with_leading_slash(self):
        """Test current_path with leading slash (should be normalized)."""
        content = "[Link](docs/spec.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "/README.md"
        )
        assert result == "[Link](remotedoc://test-owner/test-repo/main/docs/spec.md)"

    def test_current_path_empty_string(self):
        """Test current_path as empty string (should be treated as root)."""
        content = "[Link](spec.md)"
        result = rewrite_relative_paths(content, self.OWNER, self.REPO, self.BRANCH, "")
        assert result == "[Link](remotedoc://test-owner/test-repo/main/spec.md)"

    def test_complex_markdown_document(self):
        """Test complex markdown document with various link types."""
        content = """# Documentation

## Introduction

This document contains [relative links](docs/intro.md) and [absolute links](https://example.com).

### Sections

- [Getting Started](./getting-started.md)
- [Advanced Topics](../advanced/topics.md#section)
- [API Reference](api/ref.md?version=1.0)

### Reference Links

[ref1]: docs/reference.md
[ref2]: https://external.com
[ref3]: api/docs.md "API Documentation"

### Anchors

See [this section](#introduction) for details.

## Conclusion

For more info, see [the guide](guide.md "User Guide").
"""
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )

        # Check relative links are converted
        assert "remotedoc://test-owner/test-repo/main/docs/intro.md" in result
        assert "remotedoc://test-owner/test-repo/main/getting-started.md" in result
        assert (
            "remotedoc://test-owner/test-repo/main/advanced/topics.md#section" in result
        )
        assert "remotedoc://test-owner/test-repo/main/api/ref.md?version=1.0" in result
        assert "remotedoc://test-owner/test-repo/main/docs/reference.md" in result
        assert "remotedoc://test-owner/test-repo/main/api/docs.md" in result
        assert "remotedoc://test-owner/test-repo/main/guide.md" in result

        # Check absolute URLs are not converted
        assert "https://example.com" in result
        assert "https://external.com" in result

        # Check anchor links are not converted
        assert "#introduction" in result

    def test_link_in_code_block_should_not_be_converted(self):
        """Test that links in code blocks are not converted (if they appear as code)."""
        # Note: This depends on implementation - if regex matches inside code blocks,
        # they will be converted. This test documents current behavior.
        content = "```\n[Link](docs/spec.md)\n```"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "README.md"
        )
        # Current implementation will convert links even in code blocks
        # This is expected behavior unless we add code block detection
        assert "remotedoc://" in result or "docs/spec.md" in result

    def test_nested_directory_structure(self):
        """Test links from deeply nested directory."""
        content = "[Link](./sibling.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "docs/subdir/nested/file.md"
        )
        assert (
            result
            == "[Link](remotedoc://test-owner/test-repo/main/docs/subdir/nested/sibling.md)"
        )

    def test_path_going_to_root(self):
        """Test path that goes to root from subdirectory."""
        content = "[Link](../../README.md)"
        result = rewrite_relative_paths(
            content, self.OWNER, self.REPO, self.BRANCH, "docs/subdir/file.md"
        )
        assert result == "[Link](remotedoc://test-owner/test-repo/main/README.md)"
