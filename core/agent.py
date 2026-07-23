import json
from browser.vision import get_vision_hint
from core.prompt import SYSTEM_PROMPT
from browser.tools import (get_screen_state, click_element, type_into_focused,
                           press_key, go_back, wait_and_click_by_text,search_web,navigate_to_url)
from config import client,TEXT_MODEL
from browser.schema import tools_schema
from core.serializer import _serialize_assistant_message


async def run_agent(page, objective, max_steps=15):
    print(f"\n🚀 Mission Started: {objective}")

    contextualized_objective = (
        f"You are currently on this page: {page.url}\n"
        f"Task: {objective}"
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": contextualized_objective},
    ]

    # Force the very first action to be a scrape, in code, rather than trusting
    # the model to remember to look before asking questions.
    initial_scrape = await get_screen_state(page)
    messages.append({
        "role": "user",
        "content": f"[Automatic initial scrape] Here is what's currently on screen: {initial_scrape}"
    })

    recent_tool_names = []
    last_scraped_elements = initial_scrape
    vision_assist_used_this_stall = False

    # for step in range(max_steps):
    #     print(f"\n🧠 [Thinking...] Step {step + 1}")

    #     response = await client.chat.completions.create(
    #         model=TEXT_MODEL,
    #         messages=messages,
    #         tools=tools_schema,
    #         tool_choice="auto",
    #         temperature=0
    #     )

    for step in range(max_steps):
        print(f"\n🧠 [Thinking...] Step {step + 1}")

        # --- TOKEN OPTIMIZATION (CONTEXT PRUNING) ---
        api_messages = []
        
        # 1. Find the index of the absolute latest screen scrape in the history
        latest_scrape_index = -1
        for i, msg in enumerate(messages):
            content = msg.get("content") or ""
            # Detect scrapes by length and our injected JSON structure
            if isinstance(content, str) and len(content) > 1000 and '"region":' in content:
                latest_scrape_index = i
                
        # 2. Rebuild the message list for the API, nuking older scrapes
        for i, msg in enumerate(messages):
            content = msg.get("content") or ""
            if i != latest_scrape_index and isinstance(content, str) and len(content) > 1000 and '"region":' in content:
                pruned_msg = msg.copy()
                pruned_msg["content"] = "[Old screen state pruned to save tokens. Refer to the most recent scrape.]"
                api_messages.append(pruned_msg)
            else:
                api_messages.append(msg)
        # ---------------------------------------------

        response = await client.chat.completions.create(
            model=TEXT_MODEL,
            messages=api_messages,  # Pass the pruned list to the LLM
            tools=tools_schema,
            tool_choice="auto",
            temperature=0
        )

        response_message = response.choices[0].message

        # PEHLE sanitize karo
        if response_message.tool_calls:
            for tc in response_message.tool_calls:
                if '<|' in tc.function.name:
                    tc.function.name = tc.function.name.split('<|')[0].strip()

        # PHIR serialize karo (ab clean naam jaayega history mein)
        messages.append(_serialize_assistant_message(response_message))

        tool_calls = response_message.tool_calls

        if not tool_calls:
            print(f"🎉 Agent says: {response_message.content}")
            break

        for tool_call in tool_calls:
            tool_result = None
            function_name = tool_call.function.name
            try:
                function_args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                function_args = {}

            recent_tool_names.append(function_name)

            try:
                if function_name == "get_screen_state":
                    tool_result = await get_screen_state(page)
                    last_scraped_elements = tool_result
                    vision_assist_used_this_stall = False  # progress was made

                elif function_name == "click_element":
                    click_result = await click_element(page, function_args.get("target_id"))
                    fresh_state = await get_screen_state(page)
                    last_scraped_elements = fresh_state
                    tool_result = f"{click_result} Updated screen state: {fresh_state}"

                # elif function_name == "type_into_focused":
                #     tool_result = await type_into_focused(
                #         page,
                #         function_args.get("target_id"),
                #         function_args.get("text"),
                #         function_args.get("press_enter", True),
                #     )

                elif function_name == "type_into_focused":
                    press_enter = function_args.get("press_enter", True)
                    if isinstance(press_enter, str):  # "true" → True
                        press_enter = press_enter.lower() == "true"
                    
                    tool_result = await type_into_focused(
                        page,
                        function_args.get("target_id"),
                        function_args.get("text"),
                        press_enter,
                    )

                elif function_name == "search_web":
                    tool_result = await search_web(page, function_args.get("query"))
                
                elif function_name == "navigate_to_url":
                    tool_result = await navigate_to_url(page, function_args.get("url"))

                elif function_name == "press_key":
                    tool_result = await press_key(page, function_args.get("key"))

                elif function_name == "go_back":
                    go_back_result = await go_back(page)
                    fresh_state = await get_screen_state(page)
                    last_scraped_elements = fresh_state
                    tool_result = f"{go_back_result} Updated screen state: {fresh_state}"

                elif function_name == "wait_and_click_by_text":
                    tool_result = await wait_and_click_by_text(
                        page,
                        function_args.get("text_snippet"),
                        function_args.get("timeout_seconds", 15),
                    )
                
                elif function_name == "task_complete":
                    print(f"✅ Mission Complete: {function_args.get('summary')}")
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_args.get('summary', 'Task complete'),
                    })
                    return  


                else:
                    tool_result = f"Unknown tool: {function_name}"

            except Exception as e:
                tool_result = f"Tool '{function_name}' crashed: {str(e)}. Try get_screen_state again."

            if tool_result is not None:  
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": tool_result,
                })

        messages.append({
            "role": "user",
            "content": f"Current page: {page.url}. If the objective '{objective}' is now complete, call `task_complete` immediately."
        })

        # Stall detection: same tool fired 3x in a row with no resolution.
        if len(recent_tool_names) >= 3 and len(set(recent_tool_names[-3:])) == 1:
            if not vision_assist_used_this_stall:
                # First response to a stall: use the vision fallback ONCE,
                # rather than nudging blindly. This is the rare, expensive
                # path -- only triggered when text-only context has failed.
                try:
                    hint = await get_vision_hint(page, objective, last_scraped_elements)
                    messages.append({
                        "role": "user",
                        "content": f"[Vision assist -- you seem stuck] {hint}"
                    })
                    vision_assist_used_this_stall = True
                except Exception as e:
                    messages.append({
                        "role": "user",
                        "content": (
                            f"You've called '{recent_tool_names[-1]}' repeatedly with no progress "
                            f"(vision fallback also failed: {e}). Describe what you see and try "
                            "a different action."
                        )
                    })
            else:
                messages.append({
                    "role": "user",
                    "content": (
                        f"Still stuck after the vision hint. Re-read it carefully, describe what "
                        "you currently see, and try a genuinely different action."
                    )
                })

        
   

    else:
        print("⚠️ Max steps reached without the model declaring completion.")