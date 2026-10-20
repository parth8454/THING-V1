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
            "description": "Clicks an element by ID to focus it, then types text into it via real keystrokes (works on inputs, textareas, and contenteditable fields alike). Set press_enter to false if you don't want to submit (e.g. multi-line fields).For Instagram message box or similar contenteditable divs that don't appear as input fields, first use click_by_aria with pattern 'Message' to focus it, then use type_into_focused.",
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
},
{
    "type": "function",
    "function": {
        "name": "click_by_aria",
        "description": "Click an element by its aria-label using a regex pattern. Use this for dynamic elements like YouTube like/dislike/subscribe buttons where aria-label is more reliable than element ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "aria_pattern": {
                    "type": "string",
                    "description": "Regex pattern to match aria-label (e.g. 'like this video', 'subscribe', 'dislike')"
                }
            },
            "required": ["aria_pattern"]
        }
    }
},


# GitHub integration tools

{
        "type": "function",
        "function": {
            "name": "make_github_repo",
            "description": "Create a new GitHub repository under the authenticated user's account.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_name": {"type": "string", "description": "Name of the repository to create."},
                    "description": {"type": "string", "description": "Short description of the repo."},
                    "private": {"type": "boolean", "description": "Set to true for private repo, false for public."}
                },
                "required": ["repo_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "commit_github_file",
            "description": "Create or update a file in a specific GitHub repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_name": {"type": "string", "description": "Name of the repo (e.g., 'my-new-repo')."},
                    "file_path": {"type": "string", "description": "Path to the file, including filename (e.g., 'src/main.py')."},
                    "content": {"type": "string", "description": "The actual text content to write into the file."},
                    "commit_message": {"type": "string", "description": "The commit message."}
                },
                "required": ["repo_name", "file_path", "content", "commit_message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_github_file",
            "description": "Fetch the text content of a file from a GitHub repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_name": {"type": "string", "description": "Name of the repo."},
                    "file_path": {"type": "string", "description": "Path to the file."}
                },
                "required": ["repo_name", "file_path"]
            }
        }
    },{
        "type": "function",
        "function": {
            "name": "get_github_repos",
            "description": "List all GitHub repositories of the authenticated user.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_github_repo_info",
            "description": "Get detailed info about a GitHub repository — stars, forks, issues, branches, last commit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_name": {"type": "string", "description": "Name of the repo (e.g., 'my-awesome-repo')."}
                },
                "required": ["repo_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_github_branch",
            "description": "Create a new branch in a GitHub repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_name": {"type": "string", "description": "Name of the repo."},
                    "branch_name": {"type": "string", "description": "Name of the new branch you want to create (e.g., 'feature/add-login').MUST NOT contain spaces. If the user says a name with spaces (e.g., 'version 2'), you MUST automatically format it with hyphens (e.g., 'version-2') BEFORE calling this tool."},
                    "from_branch": {"type": "string", "description": "The branch you want to branch off from. Defaults to 'main'."}
                },
                "required": ["repo_name", "branch_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_github_pull_request",
            "description": "Create a pull request in a GitHub repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_name": {"type": "string", "description": "Name of the repo."},
                    "title": {"type": "string", "description": "Title of the pull request."},
                    "body": {"type": "string", "description": "Description or body text of the pull request."},
                    "head_branch": {"type": "string", "description": "The branch where your changes are (e.g., 'feature-branch')."},
                    "base_branch": {"type": "string", "description": "The branch you want to merge into. Defaults to 'main'."}
                },
                "required": ["repo_name", "title", "body", "head_branch"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "commit_github_file_to_branch",
            "description": "Commit a file to a specific branch in a GitHub repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_name": {"type": "string", "description": "Name of the repo."},
                    "file_path": {"type": "string", "description": "Path to the file, including filename (e.g., 'src/main.py')."},
                    "content": {"type": "string", "description": "The actual text content to write into the file."},
                    "commit_message": {"type": "string", "description": "The commit message."},
                    "branch": {"type": "string", "description": "The branch to commit to. Defaults to 'main'."}
                },
                "required": ["repo_name", "file_path", "content", "commit_message"]
            }
        }
    },
# ───── Fast search tool ───────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "quick_search",
            "description": "Fast web search for news, facts, or weather. CRITICAL RULE: After calling this tool and getting results, you MUST immediately call `task_complete` to give the user the answer. NEVER use `search_web` or `navigate_to_url` to verify or get more details after using this tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"]
            }
        }
    },
# ───── Memory Management ───────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "save_to_memory",
            "description": "Save ONLY pure facts, knowledge, or user preferences. NEVER save raw HTML, UI buttons, 'Skip navigation', or internal <think> processes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["user_profile", "knowledge_base"],
                        "description": "Where to store this info."
                    },
                    "key": {
                        "type": "string",
                        "description": "A short, unique identifier (e.g., '2pac_bio', 'router_pass')."
                    },
                    "value": {
                        "type": "string",
                        "description": "The exact, cleaned-up factual data to save. No filler words."
                    }
                },
                "required": ["category", "key", "value"]
            }
        }
    }

]