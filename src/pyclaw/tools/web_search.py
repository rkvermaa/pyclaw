"""Web search tool for PyClaw using Tavily or DuckDuckGo."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from langchain_core.tools import tool

if TYPE_CHECKING:
    from pyclaw.config import WebSearchConfig


def build_web_search_tool(config: WebSearchConfig):
    """Build a web search tool based on the configured provider."""
    provider = config.provider.lower()

    if provider == "tavily":
        return _build_tavily_tool(config.api_key_env)
    elif provider == "duckduckgo":
        return _build_duckduckgo_tool()
    else:
        raise ValueError(f"Unknown web search provider: {provider}")


def _build_tavily_tool(api_key_env: str):
    """Build a Tavily-based web search tool."""

    @tool
    def web_search(query: str) -> str:
        """Search the web for current information using Tavily.

        Args:
            query: The search query string.

        Returns:
            Search results as formatted text.
        """
        from tavily import TavilyClient

        api_key = os.environ.get(api_key_env, "")
        if not api_key:
            return f"Error: {api_key_env} environment variable not set."

        client = TavilyClient(api_key=api_key)
        response = client.search(query, max_results=5)

        results = []
        for r in response.get("results", []):
            title = r.get("title", "")
            url = r.get("url", "")
            content = r.get("content", "")
            results.append(f"**{title}**\n{url}\n{content}")

        if not results:
            return "No results found."

        return "\n\n---\n\n".join(results)

    return web_search


def _build_duckduckgo_tool():
    """Build a DuckDuckGo-based web search tool."""

    @tool
    def web_search(query: str) -> str:
        """Search the web for current information using DuckDuckGo.

        Args:
            query: The search query string.

        Returns:
            Search results as formatted text.
        """
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return "Error: duckduckgo-search package not installed. Install with: pip install duckduckgo-search"

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                title = r.get("title", "")
                url = r.get("href", "")
                body = r.get("body", "")
                results.append(f"**{title}**\n{url}\n{body}")

        if not results:
            return "No results found."

        return "\n\n---\n\n".join(results)

    return web_search
