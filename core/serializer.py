# 

def _serialize_assistant_message(response_message):

    """Convert the Groq SDK message object into a plain JSON-safe dict.
    Sending the raw SDK object back in `messages` is unreliable across SDK
    versions and can silently corrupt tool_calls on the next turn."""
    
    tool_calls = [
        {
            "id": tc.id,
            "type": "function",
            "function": {"name": tc.function.name, "arguments": tc.function.arguments}
        } for tc in (response_message.tool_calls or [])
    ]

    msg = {
        "role": "assistant",
        "content": response_message.content or "",
    }

    # tool_calls sirf tab add karo jab actually hoon
    if tool_calls:
        msg["tool_calls"] = tool_calls

    return msg