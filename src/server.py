"""MCP Server for markdown operations — rendering, generation, extraction, validation."""
import json
import sys
import argparse
from typing import Any, Dict, List, Optional

from .markdown_engine import MarkdownEngine


TOOL_DEFS = [
    {"name": "to_html", "description": "Convert markdown to HTML.", "inputSchema": {"type": "object", "properties": {"markdown": {"type": "string"}}, "required": ["markdown"]}},
    {"name": "generate_table", "description": "Generate a markdown table from headers and rows.", "inputSchema": {"type": "object", "properties": {"headers": {"type": "array", "items": {"type": "string"}}, "rows": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}}}, "required": ["headers"]}},
    {"name": "generate_list", "description": "Generate a markdown list (ordered or unordered).", "inputSchema": {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "string"}}, "ordered": {"type": "boolean", "default": False}}, "required": ["items"]}},
    {"name": "generate_link", "description": "Generate a markdown link.", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}, "url": {"type": "string"}, "title": {"type": "string"}}, "required": ["text", "url"]}},
    {"name": "generate_image", "description": "Generate a markdown image.", "inputSchema": {"type": "object", "properties": {"alt": {"type": "string"}, "url": {"type": "string"}, "title": {"type": "string"}}, "required": ["alt", "url"]}},
    {"name": "generate_header", "description": "Generate a markdown header (level 1-6).", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}, "level": {"type": "integer", "default": 1}}, "required": ["text"]}},
    {"name": "generate_code_block", "description": "Generate a markdown code block with optional language.", "inputSchema": {"type": "object", "properties": {"code": {"type": "string"}, "language": {"type": "string"}}, "required": ["code"]}},
    {"name": "generate_blockquote", "description": "Generate a markdown blockquote.", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
    {"name": "generate_hr", "description": "Generate a horizontal rule.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "validate", "description": "Validate markdown for common issues.", "inputSchema": {"type": "object", "properties": {"markdown": {"type": "string"}}, "required": ["markdown"]}},
    {"name": "extract_links", "description": "Extract all links from markdown.", "inputSchema": {"type": "object", "properties": {"markdown": {"type": "string"}}, "required": ["markdown"]}},
    {"name": "extract_images", "description": "Extract all images from markdown.", "inputSchema": {"type": "object", "properties": {"markdown": {"type": "string"}}, "required": ["markdown"]}},
    {"name": "extract_headers", "description": "Extract all headers from markdown with slugs.", "inputSchema": {"type": "object", "properties": {"markdown": {"type": "string"}}, "required": ["markdown"]}},
    {"name": "extract_code_blocks", "description": "Extract all code blocks from markdown.", "inputSchema": {"type": "object", "properties": {"markdown": {"type": "string"}}, "required": ["markdown"]}},
    {"name": "strip_markdown", "description": "Remove all markdown formatting, leaving plain text.", "inputSchema": {"type": "object", "properties": {"markdown": {"type": "string"}}, "required": ["markdown"]}},
    {"name": "word_count", "description": "Count words in markdown (excluding code blocks). Includes reading time estimate.", "inputSchema": {"type": "object", "properties": {"markdown": {"type": "string"}}, "required": ["markdown"]}},
]


class MCPMarkdownToolsServer:
    def __init__(self, name: str = "mcp-markdown-tools", version: str = "1.0.0"):
        self.name = name
        self.version = version

    def list_tools(self) -> List[Dict]:
        return TOOL_DEFS

    def manifest(self) -> Dict:
        return {"server": {"name": self.name, "version": self.version}, "capabilities": {"tools": {"listChanged": False}, "resources": {}, "prompts": {}}, "tools": self.list_tools()}

    def handle_tool_call(self, name: str, args: Dict[str, Any]) -> str:
        try:
            if name == "to_html":
                return json.dumps(MarkdownEngine.to_html(args["markdown"]))
            elif name == "generate_table":
                return json.dumps(MarkdownEngine.generate_table(args["headers"], args.get("rows", [])))
            elif name == "generate_list":
                return json.dumps(MarkdownEngine.generate_list(args["items"], args.get("ordered", False)))
            elif name == "generate_link":
                return json.dumps(MarkdownEngine.generate_link(args["text"], args["url"], args.get("title")))
            elif name == "generate_image":
                return json.dumps(MarkdownEngine.generate_image(args["alt"], args["url"], args.get("title")))
            elif name == "generate_header":
                return json.dumps(MarkdownEngine.generate_header(args["text"], args.get("level", 1)))
            elif name == "generate_code_block":
                return json.dumps(MarkdownEngine.generate_code_block(args["code"], args.get("language")))
            elif name == "generate_blockquote":
                return json.dumps(MarkdownEngine.generate_blockquote(args["text"]))
            elif name == "generate_hr":
                return json.dumps(MarkdownEngine.generate_hr())
            elif name == "validate":
                return json.dumps(MarkdownEngine.validate(args["markdown"]))
            elif name == "extract_links":
                return json.dumps(MarkdownEngine.extract_links(args["markdown"]))
            elif name == "extract_images":
                return json.dumps(MarkdownEngine.extract_images(args["markdown"]))
            elif name == "extract_headers":
                return json.dumps(MarkdownEngine.extract_headers(args["markdown"]))
            elif name == "extract_code_blocks":
                return json.dumps(MarkdownEngine.extract_code_blocks(args["markdown"]))
            elif name == "strip_markdown":
                return json.dumps(MarkdownEngine.strip_markdown(args["markdown"]))
            elif name == "word_count":
                return json.dumps(MarkdownEngine.word_count(args["markdown"]))
            else:
                return json.dumps({"error": f"Unknown tool: {name}"})
        except KeyError as e:
            return json.dumps({"error": f"Missing required parameter: {e}", "tool": name})
        except Exception as e:
            return json.dumps({"error": str(e), "tool": name})


def _run_stdio():
    server = MCPMarkdownToolsServer()
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try: request = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}), flush=True)
            continue
        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params", {})
        if method == "initialize":
            response = {"jsonrpc": "2.0", "id": req_id, "result": {"server": server.name, "version": server.version}}
        elif method == "tools/list":
            response = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": server.list_tools()}}
        elif method == "tools/call":
            result = server.handle_tool_call(params.get("name", ""), params.get("arguments", {}))
            response = {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": result}]}}
        elif method == "shutdown":
            response = {"jsonrpc": "2.0", "id": req_id, "result": {}}
            print(json.dumps(response), flush=True)
            break
        else:
            response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
        print(json.dumps(response), flush=True)


def main():
    parser = argparse.ArgumentParser(description="MCP Markdown Tools Server")
    parser.add_argument("--stdio", action="store_true")
    parser.add_argument("--manifest", action="store_true")
    args = parser.parse_args()
    if args.manifest:
        print(json.dumps(MCPMarkdownToolsServer().manifest(), indent=2))
    elif args.stdio:
        _run_stdio()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
