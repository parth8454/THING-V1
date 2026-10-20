# import asyncio
# import json
# from browser.vision import get_vision_hint
# from core.prompt import SYSTEM_PROMPT
# from browser.tools import (click_by_aria, get_screen_state, click_element, type_into_focused,
#                            press_key, go_back, wait_and_click_by_text,search_web,navigate_to_url)
# from config import client,TEXT_MODEL
# from browser.schema import tools_schema
# from core.serializer import _serialize_assistant_message
# from voice import listen
# from core.memory import observe_and_save


# async def run_agent(page, objective, max_steps=15, cancel_event=None):

#     if cancel_event and cancel_event.is_set():
#         print("Task cancelled!")
#         return

#     print(f"\nMission Started: {objective}")

#     contextualized_objective = (
#         f"You are currently on this page: {page.url}\n"
#         f"Task: {objective}"
#     )

#     messages = [
#         {"role": "system", "content": SYSTEM_PROMPT},
#         {"role": "user", "content": contextualized_objective},
#     ]

#     # Force the very first action to be a scrape, in code, rather than trusting
#     # the model to remember to look before asking questions.
#     initial_scrape = await get_screen_state(page)
#     messages.append({
#         "role": "user",
#         "content": f"[Automatic initial scrape] Here is what's currently on screen: {initial_scrape}"
#     })

#     recent_tool_names = []
#     last_scraped_elements = initial_scrape
#     vision_assist_used_this_stall = False

#     # for step in range(max_steps):
#     #     print(f"\n🧠 [Thinking...] Step {step + 1}")

#     #     response = await client.chat.completions.create(
#     #         model=TEXT_MODEL,
#     #         messages=messages,
#     #         tools=tools_schema,
#     #         tool_choice="auto",
#     #         temperature=0
#     #     )

#     for step in range(max_steps):

#         if cancel_event and cancel_event.is_set():
#             print("Task cancelled — naya task aa raha hai")
#             return

#         print(f"\n[Thinking...] Step {step + 1}")

#         # --- TOKEN OPTIMIZATION (CONTEXT PRUNING) ---
#         api_messages = []
        
#         # 1. Find the index of the absolute latest screen scrape in the history
#         latest_scrape_index = -1
#         for i, msg in enumerate(messages):
#             content = msg.get("content") or ""
#             # Detect scrapes by length and our injected JSON structure
#             if isinstance(content, str) and len(content) > 1000 and '"region":' in content:
#                 latest_scrape_index = i
                
#         # 2. Rebuild the message list for the API, nuking older scrapes
#         for i, msg in enumerate(messages):
#             content = msg.get("content") or ""
#             if i != latest_scrape_index and isinstance(content, str) and len(content) > 1000 and '"region":' in content:
#                 pruned_msg = msg.copy()
#                 pruned_msg["content"] = "[Old screen state pruned to save tokens. Refer to the most recent scrape.]"
#                 api_messages.append(pruned_msg)
#             else:
#                 api_messages.append(msg)
#         # ---------------------------------------------

#         response = await client.chat.completions.create(
#             model=TEXT_MODEL,
#             messages=api_messages,  # Pass the pruned list to the LLM
#             tools=tools_schema,
#             tool_choice="auto",
#             temperature=0
#         )

#         response_message = response.choices[0].message

#         # PEHLE sanitize karo
#         if response_message.tool_calls:
#             for tc in response_message.tool_calls:
#                 if '<|' in tc.function.name:
#                     tc.function.name = tc.function.name.split('<|')[0].strip()

#         # PHIR serialize karo (ab clean naam jaayega history mein)
#         messages.append(_serialize_assistant_message(response_message))

#         tool_calls = response_message.tool_calls

# # clarification to agent by user

#         if not tool_calls:
#             print(f"Agent needs clarification: {response_message.content}")
#             clarification = listen(duration=6)
#             if clarification:
#                 messages.append({"role": "user", "content": clarification})
#                 continue  # loop continue karo same task mein
#             else:
#                 break

#         for tool_call in tool_calls:
#             tool_result = None
#             function_name = tool_call.function.name
#             try:
#                 function_args = json.loads(tool_call.function.arguments or "{}")
#             except json.JSONDecodeError:
#                 function_args = {}

#             recent_tool_names.append(function_name)

#             try:
#                 if function_name == "get_screen_state":
#                     tool_result = await get_screen_state(page)
#                     last_scraped_elements = tool_result
#                     vision_assist_used_this_stall = False  # progress was made

#                     page_text = await page.evaluate('() => document.body.innerText')
#                     asyncio.create_task(observe_and_save(page_text, objective))

#                 elif function_name == "click_element":
#                     click_result = await click_element(page, function_args.get("target_id"))
#                     fresh_state = await get_screen_state(page)
#                     last_scraped_elements = fresh_state
#                     tool_result = f"{click_result} Updated screen state: {fresh_state}"

#                 # elif function_name == "type_into_focused":
#                 #     tool_result = await type_into_focused(
#                 #         page,
#                 #         function_args.get("target_id"),
#                 #         function_args.get("text"),
#                 #         function_args.get("press_enter", True),
#                 #     )

#                 elif function_name == "type_into_focused":
#                     press_enter = function_args.get("press_enter", True)
#                     if isinstance(press_enter, str):  # "true" → True
#                         press_enter = press_enter.lower() == "true"
                    
#                     tool_result = await type_into_focused(
#                         page,
#                         function_args.get("target_id"),
#                         function_args.get("text"),
#                         press_enter,
#                     )

#                 elif function_name == "search_web":
#                     tool_result = await search_web(page, function_args.get("query"))
                
#                 elif function_name == "navigate_to_url":
#                     tool_result = await navigate_to_url(page, function_args.get("url"))

#                 elif function_name == "press_key":
#                     tool_result = await press_key(page, function_args.get("key"))

#                 elif function_name == "go_back":
#                     go_back_result = await go_back(page)
#                     fresh_state = await get_screen_state(page)
#                     last_scraped_elements = fresh_state
#                     tool_result = f"{go_back_result} Updated screen state: {fresh_state}"

#                 elif function_name == "wait_and_click_by_text":
#                     tool_result = await wait_and_click_by_text(
#                         page,
#                         function_args.get("text_snippet"),
#                         function_args.get("timeout_seconds", 15),
#                     )

#                 elif function_name == "click_by_aria":
#                     tool_result = await click_by_aria(
#                     page,
#                     function_args.get("aria_pattern")
#                     )
                
#                 elif function_name == "task_complete":
#                     print(f"Mission Complete: {function_args.get('summary')}")
#                     messages.append({
#                         "tool_call_id": tool_call.id,
#                         "role": "tool",
#                         "name": function_name,
#                         "content": function_args.get('summary', 'Task complete'),
#                     })
#                     return  


#                 else:
#                     tool_result = f"Unknown tool: {function_name}"

#             except Exception as e:
#                 tool_result = f"Tool '{function_name}' crashed: {str(e)}. Try get_screen_state again."

#             if tool_result is not None:  
#                 messages.append({
#                     "tool_call_id": tool_call.id,
#                     "role": "tool",
#                     "name": function_name,
#                     "content": tool_result,
#                 })

#         messages.append({
#             "role": "user",
#             "content": f"Current page: {page.url}. If the objective '{objective}' is now complete, call `task_complete` immediately."
#         })

#         # Stall detection: same tool fired 3x in a row with no resolution.
#         if len(recent_tool_names) >= 3 and len(set(recent_tool_names[-3:])) == 1:
#             if not vision_assist_used_this_stall:
#                 # First response to a stall: use the vision fallback ONCE,
#                 # rather than nudging blindly. This is the rare, expensive
#                 # path -- only triggered when text-only context has failed.
#                 try:

#                     # inittially i used to get a ss of the page andd pass it to agent now i will just
#                     # tell the agent what to do on failure

#                     # hint = await get_vision_hint(page, objective, last_scraped_elements)
#                     # messages.append({
#                     #     "role": "user",
#                     #     "content": f"[Vision assist -- you seem stuck] {hint}"
#                     # })
#                     # vision_assist_used_this_stall = True
                    
#                     clarification = listen(duration=6)
#                     if clarification:
#                         messages.append({"role": "user", "content": clarification})
#                         continue


#                 except Exception as e:
#                     messages.append({
#                         "role": "user",
#                         "content": (
#                             f"You've called '{recent_tool_names[-1]}' repeatedly with no progress "
#                             f"(vision fallback also failed: {e}). Describe what you see and try "
#                             "a different action."
#                         )
#                     })
                    
#             else:
#                 messages.append({
#                     "role": "user",
#                     "content": (
#                         f"Still stuck after the vision hint. Re-read it carefully, describe what "
#                         "you currently see, and try a genuinely different action."
#                     )
#                 })

        
   

#     else:
#         print("⚠️ Max steps reached without the model declaring completion.")




# -------------------------------------------------------------------------------------------------------------------------------

import asyncio
import json
from urllib import response
from core.prompt import SYSTEM_PROMPT
from browser.schema import tools_schema
from core.serializer import _serialize_assistant_message
from voice import listen
from core.memory import observe_and_save
from config import client, TEXT_MODEL, PROVIDER
from fastmcp import Client as MCPClient


# ─── MCP CLIENT SETUP ─────────────────────────────────────
MCP_SERVER_URL = "http://localhost:8000/mcp"

async def call_mcp_tool(tool_name: str, args: dict) -> str:
    """Call a tool via MCP server instead of directly."""
    try:
        async with MCPClient(MCP_SERVER_URL) as mcp:
            result = await mcp.call_tool(tool_name, args)
            return result.data if hasattr(result, 'data') else str(result)
    except Exception as e:
        return f"MCP tool '{tool_name}' failed: {str(e)}"


# ─── PROVIDER-AGNOSTIC LLM CALL ───────────────────────────
async def llm_call(messages, tools):
    """Call LLM — works with Groq, OpenAI, Anthropic."""

    if PROVIDER in ("groq", "openai"):
        response = await client.chat.completions.create(
            model=TEXT_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0
        )
        return response.choices[0].message

    elif PROVIDER == "anthropic":
        # Anthropic has different API format
        # Convert OpenAI-style tools to Anthropic format
        anthropic_tools = [
            {
                "name": t["function"]["name"],
                "description": t["function"]["description"],
                "input_schema": t["function"]["parameters"]
            }
            for t in tools
        ]
        # Extract system message
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        non_system = [m for m in messages if m["role"] != "system"]

        response = await client.messages.create(
            model=TEXT_MODEL,
            max_tokens=4096,
            system=system_msg,
            messages=non_system,
            tools=anthropic_tools,
            temperature=0
        )
        return response

    elif PROVIDER == "gemini":
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=TEXT_MODEL,
            contents=[m["content"] for m in messages if m["role"] != "system"],
            config={
                "tools": [{"function_declarations": [
                    {
                        "name": t["function"]["name"],
                        "description": t["function"]["description"],
                        "parameters": {
                            "type": "object",
                            "properties": t["function"]["parameters"].get("properties", {}),
                            "required": t["function"]["parameters"].get("required", [])
                        }
                    }
                    for t in tools
                ]}],
                "temperature": 0
            }
        )
        return response

    else:
        raise ValueError(f"Unknown provider: {PROVIDER}")


def parse_tool_calls(response_message):
    """Extract tool calls from response — handles Groq/OpenAI/Anthropic formats."""
    if PROVIDER in ("groq", "openai"):
        return response_message.tool_calls or []

    elif PROVIDER == "gemini":
        tool_calls = []
        for part in response_message.parts:
            if hasattr(part, 'function_call'):
                tool_calls.append({
                    "id": "gemini_call",
                    "name": part.function_call.name,
                    "args": dict(part.function_call.args)
                })
        return tool_calls

    elif PROVIDER == "anthropic":
        tool_calls = []
        for block in response_message.content:
            if block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "args": block.input
                })
        return tool_calls

    return []


def serialize_message(response_message):
    """Serialize response for message history."""
    if PROVIDER in ("groq", "openai"):
        return _serialize_assistant_message(response_message)

    elif PROVIDER == "gemini":
        return {
            "role": "assistant",
            "content": getattr(response_message, 'text', '') or ''
        }

    elif PROVIDER == "anthropic":
        return {
            "role": "assistant",
            "content": response_message.content
        }


# ─── MAIN AGENT LOOP ──────────────────────────────────────
async def run_agent(page, objective, max_steps=15, cancel_event=None,session_history=None):

    if cancel_event and cancel_event.is_set():
        print("Task cancelled!")
        return

    print(f"\nMission Started: {objective}")

    contextualized_objective = (
        f"You are currently on this page: {page.url}\n"
        f"Task: {objective}"
    )

    messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    ]

    # Pehle history
    if session_history:
        history_text = "\n".join(session_history)
        messages.append({
            "role": "system",
            "content": f"Previous conversation context:\n{history_text}"
        })

    # Phir current objective
    messages.append({"role": "user", "content": contextualized_objective})

    # Initial scrape via MCP
    initial_scrape = await call_mcp_tool("scrape_screen", {})
    messages.append({
        "role": "user",
        "content": f"[Automatic initial scrape] Here is what's currently on screen: {initial_scrape}"
    })

    recent_tool_names = []
    last_scraped_elements = initial_scrape
    vision_assist_used_this_stall = False

    for step in range(max_steps):

        if cancel_event and cancel_event.is_set():
            print("Task cancelled — naya task aa raha hai")
            return

        print(f"\n[Thinking...] Step {step + 1}")

        # Token optimization — prune old scrapes
        api_messages = []
        latest_scrape_index = -1
        for i, msg in enumerate(messages):
            content = msg.get("content") or ""
            if isinstance(content, str) and len(content) > 1000 and ('"region":' in content or '[NAVIGATION]' in content or '[MAIN CONTENT]' in content):
                latest_scrape_index = i

        for i, msg in enumerate(messages):
            content = msg.get("content") or ""
            if i != latest_scrape_index and isinstance(content, str) and len(content) > 1000 and ('"region":' in content or '[NAVIGATION]' in content or '[MAIN CONTENT]' in content):
                pruned_msg = msg.copy()
                pruned_msg["content"] = "[Old screen state pruned to save tokens.]"
                api_messages.append(pruned_msg)
            else:
                api_messages.append(msg)

        # LLM call — provider agnostic
        response_message = await llm_call(api_messages, tools_schema)
        agent_text = serialize_message(response_message).get("content", "")
        if agent_text and agent_text.strip():
            print(f"\n🧠 Agent: {agent_text.strip()}\n")

        # Sanitize tool names (free model token leak fix)
        if PROVIDER in ("groq", "openai"):
            if response_message.tool_calls:
                for tc in response_message.tool_calls:
                    if '<|' in tc.function.name:
                        tc.function.name = tc.function.name.split('<|')[0].strip()

        messages.append(serialize_message(response_message))

        tool_calls = parse_tool_calls(response_message)

        # No tool calls — agent needs clarification
        if not tool_calls:
            print(f"Agent needs clarification: {response_message.content}")
            break

        for tool_call in tool_calls:
            tool_result = None

            # Handle both Groq/OpenAI and Anthropic formats
            if PROVIDER in ("groq", "openai"):
                function_name = tool_call.function.name
                try:
                    function_args = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    function_args = {}
                tool_call_id = tool_call.id
            else:
                function_name = tool_call["name"]
                function_args = tool_call["args"]
                tool_call_id = tool_call["id"]

            recent_tool_names.append(function_name)

            print(f"Tool Call: {function_name} | Args: {function_args}")

            try:
                # ── Route tools via MCP ──────────────────────────────
                if function_name == "get_screen_state":
                    tool_result = await call_mcp_tool("scrape_screen", {})
                    last_scraped_elements = tool_result
                    vision_assist_used_this_stall = False
                    page_text = await page.evaluate('() => document.body.innerText')
                    asyncio.create_task(observe_and_save(page_text, objective))

                elif function_name == "click_element":
                    click_result = await call_mcp_tool("click", {"target_id": function_args.get("target_id")})
                    fresh_state = await call_mcp_tool("scrape_screen", {})
                    last_scraped_elements = fresh_state
                    tool_result = f"{click_result} Updated screen state: {fresh_state}"

                elif function_name == "type_into_focused":
                    press_enter = function_args.get("press_enter", True)
                    if isinstance(press_enter, str):
                        press_enter = press_enter.lower() == "true"
                    tool_result = await call_mcp_tool("type_text", {
                        "target_id": function_args.get("target_id"),
                        "text": function_args.get("text"),
                        "press_enter": press_enter
                    })

                elif function_name == "search_web":
                    tool_result = await call_mcp_tool("web_search", {"query": function_args.get("query")})

                elif function_name == "navigate_to_url":
                    tool_result = await call_mcp_tool("go_to_url", {"url": function_args.get("url")})

                elif function_name == "press_key":
                    tool_result = await call_mcp_tool("key_press", {"key": function_args.get("key")})

                elif function_name == "go_back":
                    go_back_result = await call_mcp_tool("navigate_back", {})
                    fresh_state = await call_mcp_tool("scrape_screen", {})
                    last_scraped_elements = fresh_state
                    tool_result = f"{go_back_result} Updated screen state: {fresh_state}"

                elif function_name == "wait_and_click_by_text":
                    tool_result = await call_mcp_tool("wait_and_click", {
                        "text_snippet": function_args.get("text_snippet"),
                        "timeout_seconds": function_args.get("timeout_seconds", 15)
                    })

                elif function_name == "click_by_aria":
                    tool_result = await call_mcp_tool("click_aria", {
                        "aria_pattern": function_args.get("aria_pattern")
                    })

                elif function_name == "task_complete":
                    print(f"Mission Complete: {function_args.get('summary')}")
                    final_summary = function_args.get('summary', 'Task complete')
                    messages.append({
                        "tool_call_id": tool_call_id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_args.get('summary', 'Task complete'),
                    })
                    print(f"\nThing Says: {final_summary}\n")
                    return final_summary

                # GitHub integration tools

                elif function_name == "make_github_repo":
                    tool_result = await call_mcp_tool("make_github_repo", {
                        "repo_name": function_args.get("repo_name"),
                        "description": function_args.get("description", ""),
                        "private": function_args.get("private", True)
                    })

                elif function_name == "commit_github_file":
                    tool_result = await call_mcp_tool("commit_github_file", {
                        "repo_name": function_args.get("repo_name"),
                        "file_path": function_args.get("file_path"),
                        "content": function_args.get("content"),
                        "commit_message": function_args.get("commit_message")
                    })

                elif function_name == "fetch_github_file":
                    tool_result = await call_mcp_tool("fetch_github_file", {
                        "repo_name": function_args.get("repo_name"),
                        "file_path": function_args.get("file_path")
                    })

                elif function_name == "get_github_repos":
                    tool_result = await call_mcp_tool("get_github_repos", {})

                elif function_name == "get_github_repo_info":
                    tool_result = await call_mcp_tool("get_github_repo_info", {
                        "repo_name": function_args.get("repo_name")
                    })

                elif function_name == "create_github_branch":
                    tool_result = await call_mcp_tool("create_github_branch", {
                        "repo_name": function_args.get("repo_name"),
                        "branch_name": function_args.get("branch_name"),
                        "from_branch": function_args.get("from_branch", "main")
                    })

                elif function_name == "create_github_pull_request":
                    tool_result = await call_mcp_tool("create_github_pull_request", {
                        "repo_name": function_args.get("repo_name"),
                        "title": function_args.get("title"),
                        "body": function_args.get("body"),
                        "head_branch": function_args.get("head_branch"),
                        "base_branch": function_args.get("base_branch", "main")
                    })

                elif function_name == "commit_github_file_to_branch":
                    tool_result = await call_mcp_tool("commit_github_file_to_branch", {
                        "repo_name": function_args.get("repo_name"),
                        "file_path": function_args.get("file_path"),
                        "content": function_args.get("content"),
                        "commit_message": function_args.get("commit_message"),
                        "branch": function_args.get("branch", "main")
                    })

                # Fast search tool

                elif function_name == "quick_search":
                    tool_result = await call_mcp_tool("quick_search", {
                        "query": function_args.get("query")
                    })

                # Memory management tool

                elif function_name == "save_to_memory":
                    tool_result = await call_mcp_tool("save_to_memory", {
                        "category": function_args.get("category", "knowledge_base"),
                        "key": function_args.get("key"),
                        "value": function_args.get("value")
                    })
            
                else:
                    tool_result = f"Unknown tool: {function_name}"

            except Exception as e:
                tool_result = f"Tool '{function_name}' crashed: {str(e)}. Try get_screen_state again."

            if tool_result is not None:
                preview = str(tool_result)[:200].replace('\n', ' ')
                print(f"Tool Output: {preview}...")
                messages.append({
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(tool_result),
                })

        messages.append({
            "role": "user",
            "content": f"Current page: {page.url}. If the objective '{objective}' is now complete, call `task_complete` immediately."
        })

        # Stall detection
        if len(recent_tool_names) >= 3 and len(set(recent_tool_names[-3:])) == 1:
            if not vision_assist_used_this_stall:
                try:
                    clarification = listen(duration=6)
                    if clarification:
                        messages.append({"role": "user", "content": clarification})
                        continue
                except Exception as e:
                    messages.append({
                        "role": "user",
                        "content": f"You've called '{recent_tool_names[-1]}' repeatedly. Try a different approach."
                    })
            else:
                messages.append({
                    "role": "user",
                    "content": "Still stuck. Try a genuinely different action."
                })

    else:
        print("Max steps reached without completion.")