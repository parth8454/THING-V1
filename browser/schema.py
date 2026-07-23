# includes all the tools that are avaliable with us
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_screen_state",
            "description": "Scans the web page and returns a JSON dictionary mapping numeric IDs to interactive elements (text, tag, region). ALWAYS run this first, and re-run after any click that might have changed the page.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_element",
            "description": "Clicks an element on the screen by ID. Automatically returns a fresh screen scrape afterward.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_id": {"type": "string", "description": "The numeric ID of the element to click."}
                },
                "required": ["target_id"]
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "task_complete",
        "description": "Call this ONLY when the task is fully complete. Summarize what you did.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "What was accomplished."}
            },
            "required": ["summary"]
        }
    }
    },
    {
        "type": "function",
        "function": {
            "name": "type_into_focused",
            "description": "Clicks an element by ID to focus it, then types text into it via real keystrokes (works on inputs, textareas, and contenteditable fields alike). Set press_enter to false if you don't want to submit (e.g. multi-line fields).",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_id": {"type": "string", "description": "The numeric ID of the field to type into."},
                    "text": {"type": "string", "description": "The text to type."},
                    "press_enter": {"type": "boolean", "description": "Whether to press Enter after typing. Default true."}
                },
                "required": ["target_id", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Presses a single keyboard key, e.g. 'Escape', 'Tab', 'ArrowDown'. Useful for closing modals or navigating menus.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "The key to press."}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "go_back",
            "description": "Navigates back to the previous page. Use this if you've landed on the wrong page by mistake.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait_and_click_by_text",
            "description": "Waits for an element that appears on a DELAY (not immediately visible) and clicks it as soon as it shows up. Use this for things like video ad 'Skip' buttons, cookie-consent banners, or any prompt that only appears after a few seconds -- instead of repeatedly calling get_screen_state and hoping. Give the smallest distinctive text snippet you'd expect (e.g. 'skip', 'accept', 'continue').",
            "parameters": {
                "type": "object",
                "properties": {
                    "text_snippet": {"type": "string", "description": "Text to look for, case-insensitive substring match (e.g. 'skip', 'accept all')."},
                    "timeout_seconds": {"type": "integer", "description": "How long to wait before giving up. Default 15."}
                },
                "required": ["text_snippet"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            
            "name": "search_web",
            "description": "Search the web and gives the urls for most relevant websites. Use this as your FIRST action for ANY task that requires visiting a website. Pass a simple search query like 'youtube', 'leetcode', 'IIIT Sonepat official website'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (e.g. 'IIIT Sonepat official website')"}
                },
                "required": ["query"]
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "navigate_to_url",
        "description": "Navigate directly to a URL. Use this after search_web to go to the most relevant result.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL to navigate to."}
            },
            "required": ["url"]
        }
    }
}
]