"""
Tests for URL parser module.
"""

import pytest
from context9.url_parser import (
    parse_remotedoc_url,
    normalize_path,
    is_valid_path,
    URLParseError,
)


class TestURLParser:
    """Test cases for URL parser."""

    def test_parse_simple_url(self):
        """Test parsing a simple URL."""
        assert parse_remotedoc_url("remotedoc://spec.md") == "spec.md"

    def test_parse_nested_url(self):
        """Test parsing a nested path URL."""
        assert (
            parse_remotedoc_url("remotedoc://docs/gemini/spec.md")
            == "docs/gemini/spec.md"
        )

    def test_parse_url_with_whitespace(self):
        """Test parsing URL with whitespace."""
        assert parse_remotedoc_url("  remotedoc://spec.md  ") == "spec.md"

    def test_parse_url_with_encoding(self):
        """Test parsing URL with encoded characters."""
        assert parse_remotedoc_url("remotedoc://docs%2Fspec.md") == "docs/spec.md"

    def test_parse_invalid_scheme(self):
        """Test parsing URL with invalid scheme."""
        with pytest.raises(URLParseError, match="must start with 'remotedoc://'"):
            parse_remotedoc_url("http://spec.md")

    def test_parse_empty_url(self):
        """Test parsing empty URL."""
        with pytest.raises(URLParseError):
            parse_remotedoc_url("")

    def test_parse_url_without_path(self):
        """Test parsing URL without path."""
        with pytest.raises(URLParseError, match="must include a file path"):
            parse_remotedoc_url("remotedoc://")

    def test_normalize_path(self):
        """Test path normalization."""
        assert normalize_path("docs//gemini//spec.md") == "docs/gemini/spec.md"
        assert normalize_path("/docs/gemini/spec.md") == "docs/gemini/spec.md"
        assert normalize_path("docs/gemini/spec.md/") == "docs/gemini/spec.md"

    def test_is_valid_path(self):
        """Test path validation."""
        assert is_valid_path("spec.md") == True
        assert is_valid_path("docs/gemini/spec.md") == True
        assert is_valid_path("../spec.md") == False
        assert is_valid_path("/spec.md") == False
        assert is_valid_path("") == False
