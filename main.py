from core.agent import run_agent
import asyncio
from playwright.async_api import async_playwright

async def main():
    goal = input("Enter objective: ")
    profile_dir = input(
        "Enter path to browser profile (or leave blank): "
    ).strip()
    session_file = ""
    if not profile_dir:
        session_file = input("Enter session file path (leave blank for none): ").strip()

    async with async_playwright() as p:
        if profile_dir:
            context = await p.chromium.launch_persistent_context(
                profile_dir,
                headless=False,
                slow_mo=500,
                executable_path="/usr/bin/brave-browser"
            )
            page = context.pages[0] if context.pages else await context.new_page()
        else:
            browser = await p.chromium.launch(headless=False, slow_mo=500)
            if session_file:
                context = await browser.new_context(storage_state=session_file)
            else:
                context = await browser.new_context()
            page = await context.new_page()

        await run_agent(page, goal)

        print("\n🏁 Shutting down...")
        await page.wait_for_timeout(3000)

if __name__ == "__main__":
    asyncio.run(main())