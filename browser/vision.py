import base64
from config import VISION_MODEL,client


async def get_vision_hint(page, objective, current_elements_json):
    """Takes a screenshot and asks a vision model to identify which scraped
    element ID to act on next. Only called on stall, not every turn, so the
    extra cost/rate-limit hit is rare."""
    print("🖼️ [Vision Fallback] Capturing screenshot for a stuck agent...")
    screenshot_bytes = await page.screenshot()
    b64_image = base64.b64encode(screenshot_bytes).decode("utf-8")

    response = await client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Objective: {objective}\n\n"
                            f"Here is a screenshot of the current browser page, plus a JSON map "
                            f"of scraped interactive elements (id -> text/tag/region):\n{current_elements_json}\n\n"
                            "Look at the image and tell me, in 1-2 sentences, which element ID "
                            "the agent should click or type into next to make progress, and why. "
                            "End your reply with exactly: ELEMENT_ID: <id> (or ELEMENT_ID: none if unclear)."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64_image}"},
                    },
                ],
            }
        ],
        temperature=0,
    )
    return response.choices[0].message.content