"""Markdown operations engine — zero dependencies.

Uses only Python stdlib (re, html, json).
Provides markdown parsing, HTML rendering, table/list generation, validation.
"""
import re
import html
import json
from typing import Any, Dict, List, Optional


class MarkdownEngine:
    """Markdown operations with zero external dependencies."""

    @staticmethod
    def to_html(markdown: str) -> Dict:
        """Convert markdown to HTML."""
        lines = markdown.split("\n")
        html_parts = []
        in_code_block = False
        in_list = False
        in_ordered_list = False

        for line in lines:
            # Code block
            if line.strip().startswith("```"):
                if in_code_block:
                    html_parts.append("</code></pre>")
                    in_code_block = False
                else:
                    lang = line.strip()[3:].strip()
                    lang_attr = f' class="language-{lang}"' if lang else ""
                    html_parts.append(f'<pre><code{lang_attr}>')
                    in_code_block = True
                continue

            if in_code_block:
                html_parts.append(html.escape(line))
                continue

            # Headers
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                text = MarkdownEngine._inline_format(header_match.group(2))
                html_parts.append(f"<h{level}>{text}</h{level}>")
                continue

            # Horizontal rule
            if re.match(r'^---+$|^\*\*\*+$|^___+$', line.strip()):
                html_parts.append("<hr>")
                continue

            # Blockquote
            if line.strip().startswith(">"):
                text = MarkdownEngine._inline_format(line.strip()[1:].strip())
                html_parts.append(f"<blockquote>{text}</blockquote>")
                continue

            # Unordered list
            if re.match(r'^[\s]*[-*+]\s+', line):
                if not in_list or in_ordered_list:
                    if in_ordered_list:
                        html_parts.append("</ol>")
                    html_parts.append("<ul>")
                    in_list = True
                    in_ordered_list = False
                text = MarkdownEngine._inline_format(re.sub(r'^[\s]*[-*+]\s+', '', line))
                html_parts.append(f"<li>{text}</li>")
                continue

            # Ordered list
            if re.match(r'^[\s]*\d+\.\s+', line):
                if not in_list or not in_ordered_list:
                    if in_list and not in_ordered_list:
                        html_parts.append("</ul>")
                    html_parts.append("<ol>")
                    in_list = True
                    in_ordered_list = True
                text = MarkdownEngine._inline_format(re.sub(r'^[\s]*\d+\.\s+', '', line))
                html_parts.append(f"<li>{text}</li>")
                continue

            # Close list if we were in one
            if in_list:
                html_parts.append("</ul>" if not in_ordered_list else "</ol>")
                in_list = False
                in_ordered_list = False

            # Empty line
            if not line.strip():
                html_parts.append("")
                continue

            # Table
            if "|" in line and line.strip().startswith("|"):
                html_parts.append(MarkdownEngine._table_row_to_html(line))
                continue

            # Paragraph
            text = MarkdownEngine._inline_format(line)
            html_parts.append(f"<p>{text}</p>")

        if in_code_block:
            html_parts.append("</code></pre>")
        if in_list:
            html_parts.append("</ul>" if not in_ordered_list else "</ol>")

        return {"success": True, "html": "\n".join(html_parts), "input_length": len(markdown)}

    @staticmethod
    def _inline_format(text: str) -> str:
        """Apply inline formatting (bold, italic, code, links, images)."""
        # Bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
        # Italic
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
        # Strikethrough
        text = re.sub(r'~~(.+?)~~', r'<del>\1</del>', text)
        # Inline code
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
        # Images
        text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
        # Links
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        return text

    @staticmethod
    def _table_row_to_html(line: str) -> str:
        """Convert a markdown table row to HTML."""
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.match(r'^[-:]+$', c) for c in cells):
            return ""  # Separator row
        tds = "".join(f"<td>{c}</td>" for c in cells)
        return f"<tr>{tds}</tr>"

    @staticmethod
    def generate_table(headers: List[str], rows: List[List[str]]) -> Dict:
        """Generate a markdown table from headers and rows."""
        if not headers:
            return {"success": False, "error": "Headers cannot be empty"}

        lines = []
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in rows:
            # Pad row to match header length
            while len(row) < len(headers):
                row.append("")
            lines.append("| " + " | ".join(row) + " |")

        return {"success": True, "markdown": "\n".join(lines), "headers": len(headers), "rows": len(rows)}

    @staticmethod
    def generate_list(items: List[str], ordered: bool = False) -> Dict:
        """Generate a markdown list from items."""
        if not items:
            return {"success": False, "error": "Items list cannot be empty"}

        if ordered:
            lines = [f"{i+1}. {item}" for i, item in enumerate(items)]
        else:
            lines = [f"- {item}" for item in items]

        return {"success": True, "markdown": "\n".join(lines), "items": len(items), "ordered": ordered}

    @staticmethod
    def generate_link(text: str, url: str, title: str = None) -> Dict:
        """Generate a markdown link."""
        if title:
            return {"success": True, "markdown": f"[{text}]({url} \"{title}\")"}
        return {"success": True, "markdown": f"[{text}]({url})"}

    @staticmethod
    def generate_image(alt: str, url: str, title: str = None) -> Dict:
        """Generate a markdown image."""
        if title:
            return {"success": True, "markdown": f"![{alt}]({url} \"{title}\")"}
        return {"success": True, "markdown": f"![{alt}]({url})"}

    @staticmethod
    def generate_header(text: str, level: int = 1) -> Dict:
        """Generate a markdown header."""
        if level < 1 or level > 6:
            return {"success": False, "error": "Header level must be 1-6"}
        return {"success": True, "markdown": f"{'#' * level} {text}", "level": level}

    @staticmethod
    def generate_code_block(code: str, language: str = None) -> Dict:
        """Generate a markdown code block."""
        lang = language or ""
        return {"success": True, "markdown": f"```{lang}\n{code}\n```", "language": lang}

    @staticmethod
    def generate_blockquote(text: str) -> Dict:
        """Generate a markdown blockquote."""
        lines = text.split("\n")
        quoted = "\n".join(f"> {line}" for line in lines)
        return {"success": True, "markdown": quoted}

    @staticmethod
    def generate_hr() -> Dict:
        """Generate a horizontal rule."""
        return {"success": True, "markdown": "---"}

    @staticmethod
    def validate(markdown: str) -> Dict:
        """Basic markdown validation — checks for common issues."""
        issues = []

        # Check for unclosed code blocks
        code_fence_count = markdown.count("```")
        if code_fence_count % 2 != 0:
            issues.append("Unclosed code block (odd number of ``` fences)")

        # Check for unclosed inline code
        backtick_count = markdown.count("`") - code_fence_count * 3
        if backtick_count % 2 != 0:
            issues.append("Unclosed inline code (odd number of backticks)")

        # Check for malformed links
        if re.search(r'\[[^\]]*$', markdown) and not re.search(r'\[[^\]]*\]\([^\)]*\)', markdown):
            issues.append("Possibly malformed link (unclosed bracket)")

        # Check for header without space after #
        if re.search(r'^#[^#\s]', markdown, re.MULTILINE):
            issues.append("Header missing space after # (e.g. '#Header' should be '# Header')")

        return {
            "success": True,
            "valid": len(issues) == 0,
            "issues": issues,
            "issue_count": len(issues),
        }

    @staticmethod
    def extract_links(markdown: str) -> Dict:
        """Extract all links from markdown."""
        links = []
        # [text](url) format
        for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)(?:\s+"([^"]+)")?\)', markdown):
            links.append({"text": match.group(1), "url": match.group(2), "title": match.group(3)})
        # [ref]: url format
        for match in re.finditer(r'^\[([^\]]+)\]:\s*(.+)$', markdown, re.MULTILINE):
            links.append({"text": match.group(1), "url": match.group(2), "type": "reference"})

        return {"success": True, "links": links, "count": len(links)}

    @staticmethod
    def extract_images(markdown: str) -> Dict:
        """Extract all images from markdown."""
        images = []
        for match in re.finditer(r'!\[([^\]]*)\]\(([^)]+)(?:\s+"([^"]+)")?\)', markdown):
            images.append({"alt": match.group(1), "url": match.group(2), "title": match.group(3)})
        return {"success": True, "images": images, "count": len(images)}

    @staticmethod
    def extract_headers(markdown: str) -> Dict:
        """Extract all headers from markdown."""
        headers = []
        for match in re.finditer(r'^(#{1,6})\s+(.+)$', markdown, re.MULTILINE):
            level = len(match.group(1))
            text = match.group(2)
            headers.append({"level": level, "text": text, "slug": MarkdownEngine._slugify(text)})
        return {"success": True, "headers": headers, "count": len(headers)}

    @staticmethod
    def extract_code_blocks(markdown: str) -> Dict:
        """Extract all code blocks from markdown."""
        blocks = []
        for match in re.finditer(r'```(\w+)?\n(.*?)```', markdown, re.DOTALL):
            blocks.append({"language": match.group(1) or "plain", "code": match.group(2).strip()})
        return {"success": True, "blocks": blocks, "count": len(blocks)}

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to a URL-safe slug."""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')

    @staticmethod
    def strip_markdown(markdown: str) -> Dict:
        """Remove all markdown formatting, leaving plain text."""
        text = markdown
        # Remove code blocks
        text = re.sub(r'```[\w]*\n.*?```', '', text, flags=re.DOTALL)
        # Remove inline code
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # Remove headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # Remove bold/italic
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        # Remove strikethrough
        text = re.sub(r'~~(.+?)~~', r'\1', text)
        # Remove links (keep text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # Remove images (keep alt text)
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
        # Remove blockquotes
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
        # Remove list markers
        text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)
        # Remove horizontal rules
        text = re.sub(r'^---+$|^\*\*\*+$|^___+$', '', text, flags=re.MULTILINE)
        # Clean up extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text).strip()
        return {"success": True, "text": text, "original_length": len(markdown), "stripped_length": len(text)}

    @staticmethod
    def word_count(markdown: str) -> Dict:
        """Count words in markdown (excluding code blocks)."""
        stripped = MarkdownEngine.strip_markdown(markdown)
        words = stripped["text"].split()
        return {
            "success": True,
            "words": len(words),
            "characters": len(stripped["text"]),
            "characters_no_spaces": len(stripped["text"].replace(" ", "").replace("\n", "")),
            "lines": stripped["text"].count("\n") + 1 if stripped["text"] else 0,
            "reading_time_minutes": round(len(words) / 200, 1),  # ~200 WPM
        }
