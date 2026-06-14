"""Web search tool for PrivateClaw with multiple search backends."""

import asyncio
from typing import Optional, Type, List, Dict, Any
from pydantic import BaseModel, Field
from privateclaw.core.tools.base import PrivateClawTool


class WebSearchInput(BaseModel):
    """Input for web search tool."""
    query: str = Field(description="Search query")
    num_results: int = Field(default=5, description="Number of results to return (1-10)")


class SearchResult:
    """Represents a single search result."""

    def __init__(self, title: str, url: str, snippet: str):
        self.title = title
        self.url = url
        self.snippet = snippet

    def to_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
        }

    def __str__(self) -> str:
        return f"{self.title}\n{self.url}\n{self.snippet}"


async def _search_with_duckduckgo_lib(query: str, num_results: int = 5) -> List[SearchResult]:
    """Search using duckduckgo-search library."""
    results = []
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            search_results = list(ddgs.text(
                query,
                max_results=num_results,
                region='wt-wt'
            ))

            for r in search_results:
                results.append(SearchResult(
                    title=r.get('title', ''),
                    url=r.get('href', r.get('link', '')),
                    snippet=r.get('body', r.get('snippet', '')),
                ))
    except Exception as e:
        print(f"[WebSearch] duckduckgo-search library failed: {e}")

    return results


async def _search_with_duckduckgo_html(query: str, num_results: int = 5) -> List[SearchResult]:
    """Search using DuckDuckGo HTML scraping."""
    results = []
    try:
        import httpx
        from html.parser import HTMLParser

        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.post(url, data={"q": query}, headers=headers)
            response.raise_for_status()

            class DDGParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.results = []
                    self.current = {}
                    self.in_title = False
                    self.in_snippet = False
                    self.in_link = False

                def handle_starttag(self, tag, attrs):
                    attrs_dict = dict(attrs)
                    if tag == "a" and "result__a" in attrs_dict.get("class", ""):
                        self.in_title = True
                        self.current["url"] = attrs_dict.get("href", "")
                        self.current["title"] = ""
                    elif tag == "a" and "result__snippet" in attrs_dict.get("class", ""):
                        self.in_snippet = True
                        self.current["snippet"] = ""

                def handle_endtag(self, tag):
                    if tag == "a" and self.in_title:
                        self.in_title = False
                    elif tag == "a" and self.in_snippet:
                        self.in_snippet = False
                        if self.current.get("title"):
                            self.results.append(self.current.copy())
                        self.current = {}

                def handle_data(self, data):
                    if self.in_title:
                        self.current["title"] = self.current.get("title", "") + data
                    elif self.in_snippet:
                        self.current["snippet"] = self.current.get("snippet", "") + data

            parser = DDGParser()
            parser.feed(response.text)

            for r in parser.results[:num_results]:
                results.append(SearchResult(
                    title=r.get("title", "").strip(),
                    url=r.get("url", ""),
                    snippet=r.get("snippet", "").strip(),
                ))
    except Exception as e:
        print(f"[WebSearch] DuckDuckGo HTML scraping failed: {e}")

    return results


async def _search_with_searxng(query: str, num_results: int = 5) -> List[SearchResult]:
    """Search using public SearXNG instances."""
    results = []
    searxng_instances = [
        "https://searx.be/search",
        "https://search.bus-hit.me/search",
        "https://searx.tiekoetter.com/search",
    ]

    try:
        import httpx

        for instance in searxng_instances:
            try:
                params = {
                    "q": query,
                    "format": "json",
                    "engines": "google,bing,duckduckgo",
                }

                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(instance, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        for r in data.get("results", [])[:num_results]:
                            results.append(SearchResult(
                                title=r.get("title", ""),
                                url=r.get("url", ""),
                                snippet=r.get("content", ""),
                            ))
                        if results:
                            break
            except Exception:
                continue
    except Exception as e:
        print(f"[WebSearch] SearXNG failed: {e}")

    return results


async def _search_with_wikipedia(query: str, num_results: int = 3) -> List[SearchResult]:
    """Search Wikipedia as a fallback."""
    results = []
    try:
        import httpx

        # Search Wikipedia
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": num_results,
            "format": "json",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(search_url, params=params)
            if response.status_code == 200:
                data = response.json()
                for r in data.get("query", {}).get("search", []):
                    title = r.get("title", "")
                    snippet = r.get("snippet", "").replace('<span class="searchmatch">', '').replace('</span>', '')
                    results.append(SearchResult(
                        title=f"Wikipedia: {title}",
                        url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                        snippet=snippet,
                    ))
    except Exception as e:
        print(f"[WebSearch] Wikipedia search failed: {e}")

    return results


async def _search_multi(query: str, num_results: int = 5) -> List[SearchResult]:
    """Try multiple search backends and return combined results."""
    all_results = []

    # Try DuckDuckGo library first
    results = await _search_with_duckduckgo_lib(query, num_results)
    if results:
        return results

    # Try DuckDuckGo HTML scraping
    results = await _search_with_duckduckgo_html(query, num_results)
    if results:
        return results

    # Try SearXNG
    results = await _search_with_searxng(query, num_results)
    if results:
        return results

    # Fallback to Wikipedia
    results = await _search_with_wikipedia(query, num_results)
    if results:
        return results

    return [SearchResult(
        title="No Results",
        url="",
        snippet=f"No results found for: {query}. Try installing duckduckgo-search: pip install duckduckgo-search",
    )]


class WebSearchTool(PrivateClawTool):
    """Tool for searching the web with multiple backends.

    Features:
    - Multiple search backends (DuckDuckGo, SearXNG, Wikipedia)
    - Automatic fallback if one backend fails
    - No API key required
    - Async support
    """

    name: str = "web_search"
    description: str = (
        "Search the web for information. "
        "Use this when you need to find current information, answer questions about recent events, "
        "or research topics. Returns titles, URLs, and snippets for each result."
    )
    category: str = "search"
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str, num_results: int = 5) -> str:
        """Search the web synchronously."""
        loop = asyncio.new_event_loop()
        try:
            results = loop.run_until_complete(_search_multi(query, num_results))
        finally:
            loop.close()

        if not results:
            return f"No results found for: {query}"

        output_parts = [f"Search results for: {query}\n"]
        for i, result in enumerate(results, 1):
            output_parts.append(f"{i}. {result.title}")
            if result.url:
                output_parts.append(f"   URL: {result.url}")
            if result.snippet:
                output_parts.append(f"   {result.snippet}")
            output_parts.append("")

        return "\n".join(output_parts)

    async def _arun(self, query: str, num_results: int = 5) -> str:
        """Search the web asynchronously."""
        results = await _search_multi(query, num_results)

        if not results:
            return f"No results found for: {query}"

        output_parts = [f"Search results for: {query}\n"]
        for i, result in enumerate(results, 1):
            output_parts.append(f"{i}. {result.title}")
            if result.url:
                output_parts.append(f"   URL: {result.url}")
            if result.snippet:
                output_parts.append(f"   {result.snippet}")
            output_parts.append("")

        return "\n".join(output_parts)

    def search_structured(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Search and return structured results (for programmatic use)."""
        loop = asyncio.new_event_loop()
        try:
            results = loop.run_until_complete(_search_multi(query, num_results))
        finally:
            loop.close()

        return [r.to_dict() for r in results]
