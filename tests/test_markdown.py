"""Tests for MCP Markdown Tools — rendering, generation, extraction, validation."""
import json
import pytest
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.server import MCPMarkdownToolsServer, TOOL_DEFS
from src.markdown_engine import MarkdownEngine


class TestToolDefinitions:
    def test_all_tools_have_names(self):
        for t in TOOL_DEFS:
            assert "name" in t and len(t["name"]) > 0

    def test_all_tools_have_descriptions(self):
        for t in TOOL_DEFS:
            assert "description" in t and len(t["description"]) > 10

    def test_all_tools_have_input_schema(self):
        for t in TOOL_DEFS:
            assert "inputSchema" in t and t["inputSchema"]["type"] == "object"

    def test_expected_tool_count(self):
        assert len(TOOL_DEFS) == 16

    def test_required_tools_present(self):
        names = {t["name"] for t in TOOL_DEFS}
        expected = {"to_html", "generate_table", "generate_list", "generate_link",
                    "generate_image", "generate_header", "generate_code_block",
                    "generate_blockquote", "generate_hr", "validate",
                    "extract_links", "extract_images", "extract_headers",
                    "extract_code_blocks", "strip_markdown", "word_count"}
        assert names == expected


class TestManifest:
    def test_manifest(self):
        s = MCPMarkdownToolsServer()
        m = s.manifest()
        assert m["server"]["name"] == "mcp-markdown-tools"
        assert len(m["tools"]) == 16


class TestToHtml:
    def test_header(self):
        r = MarkdownEngine.to_html("# Hello")
        assert "<h1>" in r["html"]
        assert "Hello" in r["html"]

    def test_bold(self):
        r = MarkdownEngine.to_html("**bold text**")
        assert "<strong>" in r["html"]

    def test_italic(self):
        r = MarkdownEngine.to_html("*italic text*")
        assert "<em>" in r["html"]

    def test_code_block(self):
        r = MarkdownEngine.to_html("```python\nprint('hello')\n```")
        assert "<pre>" in r["html"]
        assert "<code" in r["html"]

    def test_list(self):
        r = MarkdownEngine.to_html("- item 1\n- item 2")
        assert "<ul>" in r["html"]
        assert "<li>" in r["html"]

    def test_ordered_list(self):
        r = MarkdownEngine.to_html("1. first\n2. second")
        assert "<ol>" in r["html"]

    def test_link(self):
        r = MarkdownEngine.to_html("[text](https://example.com)")
        assert "<a href" in r["html"]

    def test_blockquote(self):
        r = MarkdownEngine.to_html("> quoted text")
        assert "<blockquote>" in r["html"]


class TestGeneration:
    def test_table(self):
        r = MarkdownEngine.generate_table(["Name", "Age"], [["Alice", "30"], ["Bob", "25"]])
        assert "| Name | Age |" in r["markdown"]
        assert "| --- | --- |" in r["markdown"]
        assert "| Alice | 30 |" in r["markdown"]
        assert r["rows"] == 2

    def test_table_empty_headers(self):
        r = MarkdownEngine.generate_table([], [])
        assert r["success"] is False

    def test_list_unordered(self):
        r = MarkdownEngine.generate_list(["a", "b", "c"])
        assert "- a" in r["markdown"]
        assert r["ordered"] is False

    def test_list_ordered(self):
        r = MarkdownEngine.generate_list(["a", "b"], ordered=True)
        assert "1. a" in r["markdown"]
        assert "2. b" in r["markdown"]

    def test_list_empty(self):
        r = MarkdownEngine.generate_list([])
        assert r["success"] is False

    def test_link(self):
        r = MarkdownEngine.generate_link("click here", "https://example.com")
        assert r["markdown"] == "[click here](https://example.com)"

    def test_link_with_title(self):
        r = MarkdownEngine.generate_link("click", "https://example.com", "Title")
        assert '"Title"' in r["markdown"]

    def test_image(self):
        r = MarkdownEngine.generate_image("alt text", "https://example.com/img.png")
        assert "![alt text]" in r["markdown"]

    def test_header(self):
        r = MarkdownEngine.generate_header("Title", 2)
        assert r["markdown"] == "## Title"

    def test_header_invalid_level(self):
        r = MarkdownEngine.generate_header("Title", 7)
        assert r["success"] is False

    def test_code_block(self):
        r = MarkdownEngine.generate_code_block("print('hi')", "python")
        assert "```python" in r["markdown"]

    def test_blockquote(self):
        r = MarkdownEngine.generate_blockquote("quoted")
        assert "> quoted" in r["markdown"]

    def test_hr(self):
        r = MarkdownEngine.generate_hr()
        assert r["markdown"] == "---"


class TestExtraction:
    def test_extract_links(self):
        md = "Check [Google](https://google.com) and [GitHub](https://github.com)"
        r = MarkdownEngine.extract_links(md)
        assert r["count"] == 2
        assert r["links"][0]["text"] == "Google"
        assert r["links"][0]["url"] == "https://google.com"

    def test_extract_images(self):
        md = "![logo](https://example.com/logo.png)"
        r = MarkdownEngine.extract_images(md)
        assert r["count"] == 1
        assert r["images"][0]["alt"] == "logo"

    def test_extract_headers(self):
        md = "# Title\n## Section\n### Subsection"
        r = MarkdownEngine.extract_headers(md)
        assert r["count"] == 3
        assert r["headers"][0]["level"] == 1
        assert r["headers"][0]["text"] == "Title"

    def test_extract_code_blocks(self):
        md = "```python\nprint('hello')\n```\nText\n```js\nconsole.log('hi')\n```"
        r = MarkdownEngine.extract_code_blocks(md)
        assert r["count"] == 2
        assert r["blocks"][0]["language"] == "python"


class TestValidation:
    def test_valid_markdown(self):
        r = MarkdownEngine.validate("# Hello\n\nThis is **bold**.")
        assert r["valid"] is True
        assert r["issue_count"] == 0

    def test_unclosed_code_block(self):
        r = MarkdownEngine.validate("# Title\n```\ncode")
        assert r["valid"] is False
        assert "code block" in r["issues"][0].lower()

    def test_header_no_space(self):
        r = MarkdownEngine.validate("#Header without space")
        assert r["valid"] is False


class TestStripAndCount:
    def test_strip_markdown(self):
        r = MarkdownEngine.strip_markdown("**bold** and *italic*")
        assert "**" not in r["text"]
        assert "*" not in r["text"]
        assert "bold" in r["text"]

    def test_strip_code_block(self):
        r = MarkdownEngine.strip_markdown("Text\n```python\ncode\n```\nMore")
        assert "```" not in r["text"]
        assert "Text" in r["text"]

    def test_word_count(self):
        r = MarkdownEngine.word_count("Hello world this is a test")
        assert r["words"] == 6
        assert "reading_time_minutes" in r

    def test_word_count_with_code(self):
        r = MarkdownEngine.word_count("Hello\n```python\nprint('code')\n```\nWorld")
        assert r["words"] == 2  # code block excluded


class TestServerDispatch:
    def test_unknown_tool(self):
        s = MCPMarkdownToolsServer()
        assert "error" in json.loads(s.handle_tool_call("nope", {}))

    def test_missing_param(self):
        s = MCPMarkdownToolsServer()
        assert "error" in json.loads(s.handle_tool_call("to_html", {}))

    def test_to_html_dispatch(self):
        s = MCPMarkdownToolsServer()
        r = json.loads(s.handle_tool_call("to_html", {"markdown": "# Hello"}))
        assert r["success"] is True

    def test_generate_table_dispatch(self):
        s = MCPMarkdownToolsServer()
        r = json.loads(s.handle_tool_call("generate_table", {"headers": ["A", "B"], "rows": [["1", "2"]]}))
        assert r["success"] is True

    def test_word_count_dispatch(self):
        s = MCPMarkdownToolsServer()
        r = json.loads(s.handle_tool_call("word_count", {"markdown": "Hello world"}))
        assert r["words"] == 2


class TestSTDIOMode:
    def test_manifest_flag(self, capsys):
        from src.server import main
        with patch("sys.argv", ["server", "--manifest"]):
            main()
        parsed = json.loads(capsys.readouterr().out.strip())
        assert parsed["server"]["name"] == "mcp-markdown-tools"
