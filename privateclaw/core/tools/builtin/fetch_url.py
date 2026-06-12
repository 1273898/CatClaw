"""Fetch URL tool for PrivateClaw - web content retrieval with HTML cleaning."""

import re
from typing import Type, Optional
from pydantic import BaseModel, Field
from langchain_community.tools import RequestsGetTool
from privateclaw.core.tools.base import PrivateClawTool


class FetchUrlInput(BaseModel):
    """Input for fetch URL tool."""
    url: str = Field(description="URL to fetch content from")
    extract_text: bool = Field(
        default=True,
        description="Whether to extract text only (recommended) or return raw HTML"
    )


def html_to_markdown(html: str) -> str:
    """Convert HTML to clean markdown text.

    This is a lightweight converter that:
    - Removes script and style tags
    - Converts common HTML elements to markdown
    - Cleans up whitespace
    - Preserves links and structure
    """
    try:
        from bs4 import BeautifulSoup
        use_bs4 = True
    except ImportError:
        use_bs4 = False

    if use_bs4:
        return _html_to_markdown_bs4(html)
    else:
        return _html_to_markdown_regex(html)


def _html_to_markdown_bs4(html: str) -> str:
    """Convert HTML to markdown using BeautifulSoup."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'html.parser')

    # Remove script and style elements
    for element in soup(['script', 'style', 'meta', 'link', 'noscript']):
        element.decompose()

    # Convert headers
    for i in range(1, 7):
        for header in soup.find_all(f'h{i}'):
            header.replace_with(f"\n{'#' * i} {header.get_text().strip()}\n")

    # Convert links
    for link in soup.find_all('a'):
        href = link.get('href', '')
        text = link.get_text().strip()
        if href and text:
            link.replace_with(f"[{text}]({href})")

    # Convert images
    for img in soup.find_all('img'):
        alt = img.get('alt', '')
        src = img.get('src', '')
        if src:
            img.replace_with(f"![{alt}]({src})")

    # Convert bold/strong
    for bold in soup.find_all(['strong', 'b']):
        text = bold.get_text().strip()
        if text:
            bold.replace_with(f"**{text}**")

    # Convert italic/em
    for italic in soup.find_all(['em', 'i']):
        text = italic.get_text().strip()
        if text:
            italic.replace_with(f"*{text}*")

    # Convert code blocks
    for code in soup.find_all('code'):
        text = code.get_text()
        if code.parent and code.parent.name == 'pre':
            code.replace_with(f"\n```\n{text}\n```\n")
        else:
            code.replace_with(f"`{text}`")

    # Convert lists
    for ul in soup.find_all('ul'):
        items = []
        for li in ul.find_all('li', recursive=False):
            items.append(f"- {li.get_text().strip()}")
        ul.replace_with('\n'.join(items) + '\n')

    for ol in soup.find_all('ol'):
        items = []
        for i, li in enumerate(ol.find_all('li', recursive=False), 1):
            items.append(f"{i}. {li.get_text().strip()}")
        ol.replace_with('\n'.join(items) + '\n')

    # Convert paragraphs
    for p in soup.find_all('p'):
        text = p.get_text().strip()
        if text:
            p.replace_with(f"\n{text}\n")

    # Convert line breaks
    for br in soup.find_all('br'):
        br.replace_with('\n')

    # Get final text
    text = soup.get_text()

    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    text = text.strip()

    return text


def _html_to_markdown_regex(html: str) -> str:
    """Fallback regex-based HTML to text converter."""
    # Remove script and style
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    # Convert headers
    for i in range(1, 7):
        text = re.sub(
            rf'<h{i}[^>]*>(.*?)</h{i}>',
            rf'\n{"#" * i} \1\n',
            text,
            flags=re.DOTALL | re.IGNORECASE
        )

    # Convert links
    text = re.sub(
        r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
        r'[\2](\1)',
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    # Convert bold/strong
    text = re.sub(r'<(strong|b)[^>]*>(.*?)</\1>', r'**\2**', text, flags=re.DOTALL | re.IGNORECASE)

    # Convert italic/em
    text = re.sub(r'<(em|i)[^>]*>(.*?)</\1>', r'*\2*', text, flags=re.DOTALL | re.IGNORECASE)

    # Convert code
    text = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<pre[^>]*>(.*?)</pre>', r'\n```\n\1\n```\n', text, flags=re.DOTALL | re.IGNORECASE)

    # Convert paragraphs and line breaks
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', text, flags=re.DOTALL | re.IGNORECASE)

    # Remove remaining tags
    text = re.sub(r'<[^>]+>', '', text)

    # Decode HTML entities
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = text.replace('&nbsp;', ' ')

    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    text = text.strip()

    return text


class FetchUrlTool(PrivateClawTool):
    """Tool for fetching web content with HTML cleaning.

    Features:
    - Fetches web content from URLs
    - Converts HTML to clean markdown/text
    - Reduces token consumption by removing HTML noise
    - Preserves important structure (links, headers, lists)
    """

    name: str = "fetch_url"
    description: str = (
        "Fetch and read content from a web URL. "
        "Returns clean, readable text extracted from the webpage. "
        "Use this to get information from websites, documentation, or articles."
    )
    category: str = "web"
    args_schema: Type[BaseModel] = FetchUrlInput

    def __init__(self, **kwargs):
        """Initialize fetch URL tool."""
        super().__init__(**kwargs)
        self._requests_tool = RequestsGetTool(allow_dangerous_requests=True)

    def _run(self, url: str, extract_text: bool = True) -> str:
        """Fetch URL content synchronously."""
        try:
            # Fetch raw content
            raw_content = self._requests_tool.run(url)

            if not raw_content:
                return "Error: Empty response from URL"

            # Clean HTML if requested
            if extract_text:
                cleaned = html_to_markdown(raw_content)
                if not cleaned:
                    return "Error: Could not extract text from URL"
                return cleaned
            else:
                return raw_content

        except Exception as e:
            return f"Error fetching URL: {str(e)}"

    async def _arun(self, url: str, extract_text: bool = True) -> str:
        """Fetch URL content asynchronously."""
        # For now, use sync implementation
        # Can be enhanced with aiohttp for true async
        return self._run(url, extract_text)

    def get_metadata(self) -> dict:
        """Get tool metadata."""
        metadata = super().get_metadata()
        metadata.update({
            "supports_async": False,
            "html_cleaning": True,
        })
        return metadata
