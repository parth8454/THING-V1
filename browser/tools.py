import json
import asyncio
from playwright.async_api import async_playwright
from config import UI_NOISE_BLACKLIST
from config import client,TEXT_MODEL

async def get_screen_state(page):
    """Scrapes the live DOM and injects STABLE tracking IDs (assigned once, never
    reused). Returns tag/region alongside text so the model can disambiguate elements
    that share the same visible text. Works identically on any site."""
    print("👀 [Tool Run] Scraping screen and injecting IDs...")

    # for experiment remove this 2 sec cooldown
    # await page.wait_for_timeout(2000)

    elements = await page.evaluate('''() => {
        if (!window.__agentIdCounter) window.__agentIdCounter = 0;
        let interactables = document.querySelectorAll(
            'a, button, input, textarea, [role="button"], [role="link"], [contenteditable="true"]'
        );
        let result = {};
        let viewportWidth = window.innerWidth;

        interactables.forEach((el) => {
            let id = el.getAttribute('data-agent-id');
            if (!id) {
                id = (window.__agentIdCounter++).toString();
                el.setAttribute('data-agent-id', id);
            }
            let text = el.innerText || el.getAttribute('aria-label') || el.placeholder || el.value || el.name || "Unknown";
            text = text.replace(/\\n/g, ' ').trim();

            if (text.length > 0 && text !== "Unknown") {
                let rect = el.getBoundingClientRect();
                
                // --- THE FIX: STRICT VIEWPORT CULLING ---
                let isOffScreen = rect.bottom < 0 || rect.top > window.innerHeight;
                if (rect.width === 0 || rect.height === 0 || isOffScreen) return; 
                
                let region = rect.left < viewportWidth * 0.3 ? "left_panel" : "main_panel";
                let isEditable = el.getAttribute('contenteditable') === 'true'
                    || el.tagName === 'TEXTAREA' || el.tagName === 'INPUT';
                let tag = isEditable ? "editable_field" : el.tagName.toLowerCase();

                result[id] = { text: text.slice(0, 80), tag: tag, region: region };
            }
        });
        return result;
    }''')

    # OLD LOGIC FOR EXTRACTION ----------------------------------------------------------------

    # filtered = {
    #     eid: info for eid, info in elements.items()
    #     if not any(bad in info["text"].lower() for bad in UI_NOISE_BLACKLIST)
    # }

    # print(f"📄 Scraped {len(filtered)} usable elements (filtered {len(elements) - len(filtered)} noise elements)")
    # return json.dumps(filtered)

    # -----------------------------------------------------------------------------------------

    filtered = {
        eid: info for eid, info in elements.items()
        if not any(bad in info["text"].lower() for bad in UI_NOISE_BLACKLIST)
    }

    # fixed length to save token for api inference -- reduce the length of extracted to 300 
    MAX_ELEMENTS = 300
    capped_filtered = dict(list(filtered.items())[:MAX_ELEMENTS])

    print(f"📄 Scraped {len(filtered)} usable elements (Capped to {len(capped_filtered)} for token limits)")

    page_context = await page.evaluate('''() => ({
        title: document.title,
        h1: document.querySelector('h1')?.innerText || ''
    })''')

    result = {
        "page": page_context,
        "elements": capped_filtered
    }
    return json.dumps(result)

    # return json.dumps(capped_filtered)

# TOOL - 2

async def click_element(page, target_id):

    """Clicks an element based on its injected ID. Generic -- works on any site."""

    print(f"🖱️ [Tool Run] Clicking element ID: {target_id}")
    try:
        await page.locator(f'[data-agent-id="{target_id}"]').click(timeout=2000)
        return f"Successfully clicked element {target_id}."
    except Exception as e:
        return f"Error clicking element {target_id}: {str(e)}"

#  TOOL - 3

async def type_into_focused(page, target_id, text, press_enter=True):

    """Clicks the target element to focus it, then types via real keystrokes.
    Works on <input>, <textarea>, and contenteditable divs identically -- no
    site-specific knowledge of what the field is 'for'."""

    print(f"⌨️ [Tool Run] Typing '{text}' into ID: {target_id}")
    try:
        locator = page.locator(f'[data-agent-id="{target_id}"]')

        await locator.click()

        await page.keyboard.type(text, delay=8)

        if press_enter:
            await page.keyboard.press("Enter")
        return f"Successfully typed text into element {target_id}."
    except Exception as e:
        return f"Error typing into element {target_id}: {str(e)}"

# TOOL - 4

async def press_key(page, key):

    """Presses a single key (Escape, Tab, ArrowDown, etc). Generic recovery/navigation tool."""

    print(f"⌨️ [Tool Run] Pressing key: {key}")
    try:
        await page.keyboard.press(key)
        return f"Pressed key: {key}"
    except Exception as e:
        return f"Error pressing key {key}: {str(e)}"
    
# TOOL - 5

async def go_back(page):

    """Recovery tool: navigate back to previous page. Generic -- useful on any site."""

    print("↩️ [Tool Run] Going back...")
    try:
        await page.go_back(timeout=5000)
        return "Navigated back to the previous page."
    except Exception as e:
        return f"Error going back: {str(e)}"
    
# TOOL - 6 -- will review it later (may remove this thing)

async def wait_and_click_by_text(page, text_snippet, timeout_seconds=15):

    """Polls the page every 500ms for a visible, clickable element whose text
    contains `text_snippet` (case-insensitive), and clicks it the instant it
    appears. This is for anything that shows up on a DELAY rather than being
    present immediately -- ad 'Skip' buttons, cookie-consent banners, 'Accept',
    'Continue watching?' prompts, etc. Fully generic across sites; the specific
    text to look for is supplied by the model, not hardcoded per-site."""

    print(f"⏳ [Tool Run] Waiting up to {timeout_seconds}s for an element containing '{text_snippet}'...")
    deadline = asyncio.get_event_loop().time() + timeout_seconds
    snippet_lower = text_snippet.lower()

    while asyncio.get_event_loop().time() < deadline:
        try:
            found = await page.evaluate('''(snippet) => {
                const all = document.querySelectorAll(
                    'a, button, [role="button"], [contenteditable="true"], span, div'
                );
                for (const el of all) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) continue;
                    const text = (el.innerText || el.getAttribute('aria-label') || '').trim();
                    if (text.toLowerCase().includes(snippet)) {
                        let id = el.getAttribute('data-agent-id');
                        if (!id) {
                            if (!window.__agentIdCounter) window.__agentIdCounter = 0;
                            id = (window.__agentIdCounter++).toString();
                            el.setAttribute('data-agent-id', id);
                        }
                        return id;
                    }
                }
                return null;
            }''', snippet_lower)
        except Exception:
            found = None

        if found:
            try:
                await page.locator(f'[data-agent-id="{found}"]').click(timeout=3000)
                return f"Found and clicked element containing '{text_snippet}' (waited less than {timeout_seconds}s)."
            except Exception as e:
                return f"Found element containing '{text_snippet}' but clicking failed: {str(e)}"

        await page.wait_for_timeout(5000)

    return f"No element containing '{text_snippet}' appeared within {timeout_seconds}s. It may not exist on this page, or may need more time."

async def search_web(page, query):
    print(f"🔍 Searching: {query}")
    await page.goto(f"https://duckduckgo.com/?q={query}")
    await page.wait_for_timeout(2000)
    
    urls = await page.evaluate('''() => {
        const results = [];
        document.querySelectorAll('a[href]').forEach(el => {
            const href = el.getAttribute('href');
            const text = el.innerText.trim();
            if (href && href.startsWith('http') && 
                !href.includes('google.com') && 
                !href.includes('accounts.') && text) {
                results.push({ text: text.slice(0, 60), url: href });
            }
        });
        return results.slice(0, 8);
    }''')
    
    return (
    f"Search results for '{query}':\n{json.dumps(urls, indent=2)}\n\n"
    f"NEXT STEP: You MUST now call navigate_to_url with the most relevant URL above. "
    f"Do not call search_web again."
)

async def navigate_to_url(page, url):
    print(f"🌐 Navigating to: {url}")
    await page.goto(url)
    fresh_state = await get_screen_state(page)
    return f"Navigated to {url}. Screen: {fresh_state}"
