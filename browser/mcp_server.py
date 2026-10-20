from fastmcp import FastMCP
from playwright.async_api import async_playwright

# Existing tools for GitHub integration
from capabilities.github_tools import *

# memory management
from capabilities.memory_manager import save_to_memory

# Existing tools for browser automation
from browser.tools import (
    get_screen_state,
    click_element,
    type_into_focused,
    press_key,
    go_back,
    wait_and_click_by_text,
    search_web,
    navigate_to_url,
    click_by_aria
)

mcp = FastMCP("THING-V1-Browser")

# Global page object — shared across tools
_page = None

async def get_page():
    """Get or create browser page via CDP"""
    global _page
    if _page is None:
        from playwright.async_api import async_playwright
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        _page = context.pages[0] if context.pages else await context.new_page()
    return _page

# ─── MCP TOOLS ────────────────────────────────────────────

@mcp.tool()
async def scrape_screen() -> str:
    """Scrape the current browser page and return structured layout with all interactive elements grouped by section (NAVIGATION, HEADER, SEARCH, MAIN CONTENT, SIDEBAR). Always call this first before any action."""
    page = await get_page()
    return await get_screen_state(page)

@mcp.tool()
async def click(target_id: str) -> str:
    """Click an element on the page by its ID from the screen state. Get IDs from scrape_screen first."""
    page = await get_page()
    return await click_element(page, target_id)

@mcp.tool()
async def click_aria(aria_pattern: str) -> str:
    """Click an element by aria-label regex pattern. Use for YouTube like/dislike/subscribe buttons and Instagram actions where IDs are unstable."""
    page = await get_page()
    return await click_by_aria(page, aria_pattern)

@mcp.tool()
async def type_text(target_id: str, text: str, press_enter: bool = True) -> str:
    """Click a field by ID and type text into it. Set press_enter=False for multi-line fields."""
    page = await get_page()
    return await type_into_focused(page, target_id, text, press_enter)

@mcp.tool()
async def key_press(key: str) -> str:
    """Press a keyboard key. Examples: 'Escape', 'Tab', 'ArrowDown', 'Enter', '/'"""
    page = await get_page()
    return await press_key(page, key)

@mcp.tool()
async def navigate_back() -> str:
    """Navigate to the previous page in browser history."""
    page = await get_page()
    return await go_back(page)

@mcp.tool()
async def web_search(query: str) -> str:
    """Search DuckDuckGo and return top URLs. Use this first for any task that needs visiting a website."""
    page = await get_page()
    return await search_web(page, query)

@mcp.tool()
async def go_to_url(url: str) -> str:
    """Navigate directly to a URL. Use after web_search to open the most relevant result."""
    page = await get_page()
    return await navigate_to_url(page, url)

@mcp.tool()
async def wait_and_click(text_snippet: str, timeout_seconds: int = 15) -> str:
    """Wait for a delayed element to appear (like YouTube skip ad button) and click it. Use for elements that appear after a few seconds."""
    page = await get_page()
    return await wait_and_click_by_text(page, text_snippet, timeout_seconds)

@mcp.tool()
async def get_current_url() -> str:
    """Get the current page URL."""
    page = await get_page()
    return page.url

# ─── GitHub integration tools ───────────────────────────────────────────

@mcp.tool()
async def make_github_repo(repo_name: str, description: str = "", private: bool = True) -> str:
    """Create a new GitHub repository."""
    return await create_github_repo(repo_name, description, private)

@mcp.tool()
async def commit_github_file(repo_name: str, file_path: str, content: str, commit_message: str) -> str:
    """Create or update a file in a GitHub repository."""
    return await create_or_update_file(repo_name, file_path, content, commit_message)

@mcp.tool()
async def fetch_github_file(repo_name: str, file_path: str) -> str:
    """Fetch the text content of a file from a GitHub repository."""
    return await get_file_content(repo_name, file_path)

@mcp.tool()
async def get_github_repos() -> str:
    """List all GitHub repositories of the authenticated user."""
    return await list_repos()

@mcp.tool()
async def get_github_repo_info(repo_name: str) -> str:
    """Get detailed info about a GitHub repository — stars, forks, issues, branches, last commit."""
    return await get_repo_info(repo_name)

@mcp.tool()
async def create_github_branch(repo_name: str, branch_name: str, from_branch: str = "main") -> str:
    """Create a new branch in a GitHub repository."""
    return await create_branch(repo_name, branch_name, from_branch)

@mcp.tool()
async def create_github_pull_request(repo_name: str, title: str, body: str, head_branch: str, base_branch: str = "main") -> str:
    """Create a pull request in a GitHub repository."""
    return await create_pull_request(repo_name, title, body, head_branch, base_branch)

@mcp.tool()
async def commit_github_file_to_branch(repo_name: str, file_path: str, content: str, commit_message: str, branch: str = "main") -> str:
    """Commit a file to a specific branch in a GitHub repository."""
    return await commit_file(repo_name, file_path, content, commit_message, branch)

# ─── Fast search tool ───────────────────────────────────────────

from capabilities.fast_search import quick_web_search

@mcp.tool()
async def quick_search(query: str) -> str:
    """Use this FIRST for general knowledge, news, current events, or weather queries. Returns fast text results without opening the browser."""
    return await quick_web_search(query)

# ─── Memory Management ───────────────────────────────────────────
@mcp.tool(name="save_to_memory")
def mcp_save_to_memory(category: str, key: str, value: str) -> str:
    """Save clean facts to long-term JSON memory."""
    print(f"Memory Injecting: [{category}] {key}")
    return save_to_memory(category, key, value)
# ─── RUN SERVER ───────────────────────────────────────────

if __name__ == "__main__":
    print("THING-V1 MCP server starting...")
    print("Connecting to brave on port 9222...")
    mcp.run(transport="http")