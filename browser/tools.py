import json
import asyncio
from playwright.async_api import async_playwright
from config import UI_NOISE_BLACKLIST
from config import client,TEXT_MODEL

# async def get_screen_state(page):
#     """Scrapes the live DOM and injects STABLE tracking IDs (assigned once, never
#     reused). Returns tag/region alongside text so the model can disambiguate elements
#     that share the same visible text. Works identically on any site."""
#     print("[Tool Run] Scraping screen and injecting IDs...")

#     # for experiment remove this 2 sec cooldown
#     # await page.wait_for_timeout(2000)

#     elements = await page.evaluate('''() => {
#         if (!window.__agentIdCounter) window.__agentIdCounter = 0;
#         let interactables = document.querySelectorAll(
#             'a, button, input, textarea, [role="button"], [role="link"], [contenteditable="true"]'
#         );
#         let result = {};
#         let viewportWidth = window.innerWidth;

#         interactables.forEach((el) => {
#             let id = el.getAttribute('data-agent-id');
#             if (!id) {
#                 id = (window.__agentIdCounter++).toString();
#                 el.setAttribute('data-agent-id', id);
#             }
#             let text = el.innerText || el.getAttribute('aria-label') || el.placeholder || el.value || el.name || "Unknown";
#             text = text.replace(/\\n/g, ' ').trim();

#             if (text.length > 0 && text !== "Unknown") {
#                 let rect = el.getBoundingClientRect();
                
#                 // --- THE FIX: STRICT VIEWPORT CULLING ---
#                 let isOffScreen = rect.bottom < 0 || rect.top > window.innerHeight;
#                 if (rect.width === 0 || rect.height === 0 || isOffScreen) return; 
                
#                 let region = rect.left < viewportWidth * 0.3 ? "left_panel" : "main_panel";
#                 let isEditable = el.getAttribute('contenteditable') === 'true'
#                     || el.tagName === 'TEXTAREA' || el.tagName === 'INPUT';
#                 let tag = isEditable ? "editable_field" : el.tagName.toLowerCase();

#                 result[id] = { text: text.slice(0, 80), tag: tag, region: region };
#             }
#         });
#         return result;
#     }''')

#     # OLD LOGIC FOR EXTRACTION ----------------------------------------------------------------

#     # filtered = {
#     #     eid: info for eid, info in elements.items()
#     #     if not any(bad in info["text"].lower() for bad in UI_NOISE_BLACKLIST)
#     # }

#     # print(f"Scraped {len(filtered)} usable elements (filtered {len(elements) - len(filtered)} noise elements)")
#     # return json.dumps(filtered)

#     # -----------------------------------------------------------------------------------------

#     filtered = {
#         eid: info for eid, info in elements.items()
#         if not any(bad in info["text"].lower() for bad in UI_NOISE_BLACKLIST)
#     }

#     # fixed length to save token for api inference -- reduce the length of extracted to 300 
#     MAX_ELEMENTS = 300
#     capped_filtered = dict(list(filtered.items())[:MAX_ELEMENTS])

#     print(f"Scraped {len(filtered)} usable elements (Capped to {len(capped_filtered)} for token limits)")

#     page_context = await page.evaluate('''() => ({
#         title: document.title,
#         h1: document.querySelector('h1')?.innerText || ''
#     })''')

#     result = {
#         "page": page_context,
#         "elements": capped_filtered
#     }
#     return json.dumps(result)

    # return json.dumps(capped_filtered)

async def get_screen_state(page):
    """Scrapes the live DOM and injects STABLE tracking IDs (assigned once, never
    reused). Returns structured sections so LLM can understand page layout better."""
    print("[Tool Run] Scraping screen and injecting IDs...")

    elements = await page.evaluate(r'''() => {
        if (!window.__agentIdCounter) window.__agentIdCounter = 0;

        let interactables = document.querySelectorAll(
        // Native elements
        'a, button, input, textarea, select, ' +
        // ARIA roles
        '[role="button"], [role="link"], [role="textbox"], [role="checkbox"], ' +
        '[role="radio"], [role="menuitem"], [role="tab"], [role="option"], ' +
        '[role="switch"], [role="combobox"], [role="searchbox"], ' +
        // Contenteditable
        '[contenteditable="true"] ' +
        // Click handlers — most interactive divs/spans
        '[onclick], [tabindex="0"], ' +
        // Common patterns
        'label[for], [type="submit"], [type="button"], [type="reset"]'
    );

        let result = {};
        let viewportWidth = window.innerWidth;

        function getSection(el) {
            // 1. Semantic HTML tags
            if (el.closest('nav'))    return 'NAVIGATION';
            if (el.closest('header')) return 'HEADER';
            if (el.closest('form'))   return 'FORM';
            if (el.closest('aside'))  return 'SIDEBAR';
            if (el.closest('footer')) return 'FOOTER';
            if (el.closest('main'))   return 'MAIN CONTENT';

            // 2. ARIA roles
            let role = el.getAttribute('role') || '';
            let ancestor = el.parentElement;
            while (ancestor) {
                let ar = ancestor.getAttribute('role') || '';
                if (ar === 'navigation') return 'NAVIGATION';
                if (ar === 'search')     return 'SEARCH';
                if (ar === 'banner')     return 'HEADER';
                if (ar === 'main')       return 'MAIN CONTENT';
                if (ar === 'complementary') return 'SIDEBAR';
                if (ar === 'contentinfo')   return 'FOOTER';
                ancestor = ancestor.parentElement;
            }

            // 3. CSS class/id hints
            let fullClass = el.className + ' ' + (el.id || '');
            let parentEl = el.parentElement;
            for (let i = 0; i < 5 && parentEl; i++) {
                fullClass += ' ' + parentEl.className + ' ' + (parentEl.id || '');
                parentEl = parentEl.parentElement;
            }
            fullClass = fullClass.toLowerCase();

            if (/nav|menu|navbar/.test(fullClass))      return 'NAVIGATION';
            if (/search/.test(fullClass))               return 'SEARCH';
            if (/sidebar|side-bar|side_bar/.test(fullClass)) return 'SIDEBAR';
            if (/header|top-bar/.test(fullClass))       return 'HEADER';
            if (/footer/.test(fullClass))               return 'FOOTER';
            if (/modal|dialog|popup/.test(fullClass))   return 'MODAL';

            // 4. X position fallback
            let rect = el.getBoundingClientRect();
            return rect.left < viewportWidth * 0.3 ? 'SIDEBAR' : 'MAIN CONTENT';
        }

        interactables.forEach((el) => {
            let id = el.getAttribute('data-agent-id');
            if (!id) {
                id = (window.__agentIdCounter++).toString();
                el.setAttribute('data-agent-id', id);
            }


         // let text = el.innerText 
         // || el.getAttribute('aria-label') 
         // || el.querySelector('[aria-label]')?.getAttribute('aria-label')  // ← add karo
         // || el.getAttribute('aria-placeholder')
         // || el.placeholder 
         // || el.value 
         // || el.name 
         // || "Unknown";

            let ariaPlaceholder = el.getAttribute('aria-placeholder');
            let text = el.innerText 
                || el.getAttribute('aria-label')
                || el.querySelector('[aria-label]')?.getAttribute('aria-label')
                || (ariaPlaceholder ? '[input] ' + ariaPlaceholder : '')
                || el.placeholder 
                || el.value 
                || el.name 
                || "Unknown";


            text = text.replace(/[\n\r]/g, ' ').trim();

            if (text.length > 0 && text !== "Unknown") {
                let rect = el.getBoundingClientRect();
                let isOffScreen = rect.bottom < 0 || rect.top > window.innerHeight;
                if (rect.width === 0 || rect.height === 0 || isOffScreen) return;

                let isEditable = el.getAttribute('contenteditable') === 'true'
                    || el.tagName === 'TEXTAREA' || el.tagName === 'INPUT';
                let tag = isEditable ? 'input' : el.tagName.toLowerCase();
                let section = getSection(el);

                result[id] = { text: text.slice(0, 80), tag: tag, section: section };
            }
        });

        return result;
    }''')

    # Filter noise
    filtered = {
        eid: info for eid, info in elements.items()
        if not any(bad in info["text"].lower() for bad in UI_NOISE_BLACKLIST)
    }

    MAX_ELEMENTS = 300
    capped = dict(list(filtered.items())[:MAX_ELEMENTS])

    print(f"Scraped {len(filtered)} usable elements (Capped to {len(capped)} for token limits)")

    # Page context
    page_context = await page.evaluate('''() => ({
        title: document.title,
        url: window.location.href,
        h1: document.querySelector('h1')?.innerText || ''
    })''')

    # Group elements by section
    sections = {}
    for eid, info in capped.items():
        sec = info["section"]
        if sec not in sections:
            sections[sec] = []
        sections[sec].append((eid, info["text"], info["tag"]))

    # Build structured text output
    lines = []
    lines.append(f"PAGE: {page_context['title']}")
    lines.append(f"URL: {page_context['url']}")
    if page_context['h1']:
        lines.append(f"H1: {page_context['h1']}")
    lines.append("")

    # Section order
    order = ["NAVIGATION", "HEADER", "SEARCH", "FORM", "MAIN CONTENT", "SIDEBAR", "MODAL", "FOOTER"]
    all_sections = order + [s for s in sections if s not in order]

    for sec in all_sections:
        if sec not in sections:
            continue
        lines.append(f"[{sec}]")
        for eid, text, tag in sections[sec]:
            lines.append(f"  {eid} | {text} | {tag}")
        lines.append("")

    structured_output = "\n".join(lines)

    print("\n--- SCREEN STATE ---")
    print(structured_output)
    print("--- END SCREEN STATE ---\n")

    return structured_output

# TOOL - 2

async def click_element(page, target_id):

    """Clicks an element based on its injected ID. Generic -- works on any site."""

    print(f"[Tool Run] Clicking element ID: {target_id}")
    try:
        await page.locator(f'[data-agent-id="{target_id}"]').click(timeout=2000)

        await page.wait_for_load_state("domcontentloaded", timeout=3000)
        return f"Successfully clicked element {target_id}."
    except Exception as e:
        return f"Error clicking element {target_id}: {str(e)}"

#  TOOL - 3

async def type_into_focused(page, target_id, text, press_enter=True):

    """Clicks the target element to focus it, then types via real keystrokes.
    Works on <input>, <textarea>, and contenteditable divs identically -- no
    site-specific knowledge of what the field is 'for'."""

    print(f"[Tool Run] Typing '{text}' into ID: {target_id}")
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

    print(f"[Tool Run] Pressing key: {key}")
    try:
        await page.keyboard.press(key)
        return f"Pressed key: {key}"
    except Exception as e:
        return f"Error pressing key {key}: {str(e)}"
    
# TOOL - 5

async def go_back(page):

    """Recovery tool: navigate back to previous page. Generic -- useful on any site."""

    print("[Tool Run] Going back...")
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

    print(f"[Tool Run] Waiting up to {timeout_seconds}s for an element containing '{text_snippet}'...")
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
    print(f"Searching: {query}")
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
    print(f"Navigating to: {url}")
    await page.goto(url)
    fresh_state = await get_screen_state(page)
    return f"Navigated to {url}. Screen: {fresh_state}"


async def click_by_aria(page, aria_pattern):
    """Click element by aria-label pattern — more reliable than ID for dynamic elements like YouTube like/dislike buttons."""
    print(f"🎯 [Tool Run] Clicking by aria: '{aria_pattern}'")
    try:
        result = await page.evaluate(f'''() => {{
            const pattern = /{aria_pattern}/i;
            const all = document.querySelectorAll('button, a, [role="button"]');
            for (const el of all) {{
                const aria = el.getAttribute('aria-label') || '';
                if (pattern.test(aria)) {{
                    el.click();
                    return {{ ok: true, aria: aria }};
                }}
            }}
            return {{ ok: false }};
        }}''')
        
        if result['ok']:
            return f"✅ Clicked element with aria-label matching '{aria_pattern}': {result['aria']}"
        else:
            return f"❌ No element found with aria-label matching '{aria_pattern}'"
    except Exception as e:
        return f"Error: {str(e)}"