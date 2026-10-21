# from core.agent import run_agent
# import asyncio
# from playwright.async_api import async_playwright
# from voice import listen

# async def main():
#     mode = "v".strip().lower()

#     if mode == "v":
#         goal = listen(duration=5)
#         if not goal:
#             print("Nothing heard. Switching to text input.")
#             goal = input("Enter objective: ")
#     else:
#         goal = input("Enter objective: ")

#     profile_dir = ""

#     # profile_dir = input(
#     #     "Enter path to browser profile (or leave blank): "
#     # ).strip()
#     session_file = ""
#     # if not profile_dir:
#     #     session_file = input("Enter session file path (leave blank for none): ").strip()

#     async with async_playwright() as p:
        
#         if profile_dir:
#             context = await p.chromium.launch_persistent_context(
#                 profile_dir,
#                 headless=False,
#                 slow_mo=500,
#                 executable_path="/usr/bin/brave-browser"
#             )
#             page = context.pages[0] if context.pages else await context.new_page()
#         else:
#             browser = await p.chromium.launch(headless=False, slow_mo=500)
#             if session_file:
#                 context = await browser.new_context(storage_state=session_file)
#             else:
#                 context = await browser.new_context()
#             page = await context.new_page()

#         await run_agent(page, goal)

#         print("\nShutting down...")
#         await page.wait_for_timeout(3000)

# if __name__ == "__main__":
#     asyncio.run(main())

# -------------------------------------------------------------------------------------------

# from core.agent import run_agent
# import asyncio
# from playwright.async_api import async_playwright
# from voice import listen

# async def main():
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=False, slow_mo=500)
#         context = await browser.new_context()
#         page = await context.new_page()

#         print("Agent ready! Bol kya karna hai (ya 'band karo' bol ke exit kar)")

#         while True:
#             goal = listen(duration=6)

#             if not goal:
#                 print("cant listen, say it again?")
#                 continue

#             if any(x in goal.lower() for x in ["band karo", "exit", "quit", "stop", "bye"]):
#                 print("Theek hai, band kar raha hoon...")
#                 break

#             await run_agent(page, goal)
#             print("\nTask done! Agla kaam bol...")

#         print("\nShutting down...")
#         await page.wait_for_timeout(2000)

# if __name__ == "__main__":
#     asyncio.run(main())

# ----------------------------------------------------------------------------------------

# from core.agent import run_agent
# import asyncio
# import threading
# import subprocess
# import tempfile
# import os
# from playwright.async_api import async_playwright
# from faster_whisper import WhisperModel
# from pynput import keyboard

# model = WhisperModel("small", device="cuda", compute_type="int8")
# MIC_SOURCE = "alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__Mic1__source"
# PUSH_KEY = keyboard.Key.caps_lock

# is_recording = False

# def record_and_transcribe():
#     tmp_path = tempfile.mktemp(suffix=".wav")
#     print("\nRecording... CapsLock chodo rokne ke liye")
#     rec = subprocess.Popen(["pw-record", "--target", MIC_SOURCE, tmp_path])

#     done = threading.Event()
#     def on_release(key):
#         if key == PUSH_KEY:
#             done.set()
#             return False
#     with keyboard.Listener(on_release=on_release):
#         done.wait()

#     rec.terminate()
#     rec.wait()

#     print("Transcribing...")
#     segments, _ = model.transcribe(tmp_path, language="en")
#     text = " ".join(seg.text.strip() for seg in segments).strip()
#     if os.path.exists(tmp_path):
#         os.unlink(tmp_path)
#     print(f"Suna: '{text}'")
#     return text

# session_history = []

# async def main():
#     global is_recording
#     global session_history
#     pending = {"goal": None}
#     new_task = asyncio.Event()
#     cancel_event = asyncio.Event()
#     loop = asyncio.get_event_loop()

#     def on_press(key):
#         global is_recording
#         if key == PUSH_KEY and not is_recording:
#             is_recording = True
#             pending["goal"] = None
#             def _record():
#                 global is_recording
#                 goal = record_and_transcribe()
#                 is_recording = False
#                 if goal:    
#                     pending["goal"] = goal
#                     asyncio.run_coroutine_threadsafe(_notify(), loop)
#             threading.Thread(target=_record, daemon=True).start()

#     async def _notify():
#         cancel_event.set()  # current task cancel karo
#         new_task.clear()
#         new_task.set()

#     listener = keyboard.Listener(on_press=on_press)
#     listener.start()

#     async with async_playwright() as p:
#     # Nayi instance nahi — existing Brave se connect
#         browser = await p.chromium.connect_over_cdp("http://localhost:9222")
#         context = browser.contexts[0]
#         page = context.pages[0] if context.pages else await context.new_page()

#         print("\nAgent ready!")
#         print("press CapsLock  → speak → CapsLock release → task started!\n")

#         while True:
#             await new_task.wait()
#             new_task.clear()

#             goal = pending["goal"]
#             pending["goal"] = None

#             if not goal:
#                 continue

#             if any(x in goal.lower() for x in ["band karo", "exit", "quit", "stop", "bye"]):
#                 print("Band kar raha hoon...")
#                 listener.stop()
#                 break

#             cancel_event.clear()  # naya task shuru — cancel reset

#             final_answer = await run_agent(page, goal, cancel_event=cancel_event, session_history=session_history)

#             if final_answer and not cancel_event.is_set():
#                 session_history.append(f"User: {goal}")
#                 session_history.append(f"Agent: {final_answer}")
                
#                 # 3. Token limit bachaane ke liye sirf last 8 lines (4 turns) yaad rakh
#                 if len(session_history) > 8:
#                     session_history = session_history[-8:]

#             # lets try to reset the agent ID counter in the page context -- 
#             # to improve the agent accuracy and prevent it from getting stuck in loops

#             await page.evaluate('() => { window.__agentIdCounter = 0; }')

#             print(f"\nDone! CapsLock dabao agla kaam bolne ke liye")

#         print("\nShutting down...")
#         await page.wait_for_timeout(2000)

# if __name__ == "__main__":
#     asyncio.run(main())

from core.agent import run_agent
import asyncio
import threading
import subprocess
import tempfile
import os
import aiohttp
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from playwright.async_api import async_playwright
from faster_whisper import WhisperModel
from pynput import keyboard

from capabilities.memory_manager import init_memory, save_to_memory, read_memory

# --- 1. FastAPI Setup ---
app = FastAPI()

class CommandRequest(BaseModel):
    command: str
    sender_id: str

# --- 2. Global State (API aur Playwright dono ke liye) ---
pending = {"goal": None, "source": None, "sender_id": None}
new_task = asyncio.Event()
cancel_event = asyncio.Event()
session_history = []
is_recording = False
loop = None # Will be set in main()

model = WhisperModel("small", device="cuda", compute_type="int8")
MIC_SOURCE = "alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__Mic1__source"
PUSH_KEY = keyboard.Key.caps_lock

# --- 3. API Endpoint (WhatsApp to THING) ---
@app.post("/api/command")
async def receive_command(req: CommandRequest):
    global pending, new_task, cancel_event
    print(f"\n[API] Received command from {req.sender_id}: {req.command}")
    
    pending["goal"] = req.command
    pending["source"] = "whatsapp"
    pending["sender_id"] = req.sender_id
    
    # Current task roko aur naya shuru karo
    cancel_event.set()
    new_task.clear()
    new_task.set()
    
    return {"status": "Command queued for execution"}

@app.on_event("startup")
async def startup_event():
    init_memory()
    print("🧠 Memory Vault Initialized!")

# --- Mic Recording Logic ---
def record_and_transcribe():
    tmp_path = tempfile.mktemp(suffix=".wav")
    print("\nRecording... CapsLock chodo rokne ke liye")
    rec = subprocess.Popen(["pw-record", "--target", MIC_SOURCE, tmp_path])

    done = threading.Event()
    def on_release(key):
        if key == PUSH_KEY:
            done.set()
            return False
    with keyboard.Listener(on_release=on_release):
        done.wait()

    rec.terminate()
    rec.wait()

    print("Transcribing...")
    segments, _ = model.transcribe(tmp_path, language="en")
    text = " ".join(seg.text.strip() for seg in segments).strip()
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)
    print(f"Suna: '{text}'")
    return text

async def main():
    global is_recording, session_history, loop, pending
    loop = asyncio.get_event_loop()

    # --- Start FastAPI in Background ---
    config = uvicorn.Config(app, host="127.0.0.1", port=8001, log_level="error")
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())
    print("FastAPI Server running on port 8001 (Ghost Mode ON)")

    # --- Keyboard Listener (Mic to THING) ---
    def on_press(key):
        global is_recording, pending
        if key == PUSH_KEY and not is_recording:
            is_recording = True
            def _record():
                global is_recording, pending
                goal = record_and_transcribe()
                is_recording = False
                if goal:    
                    pending["goal"] = goal
                    pending["source"] = "mic"
                    pending["sender_id"] = None
                    asyncio.run_coroutine_threadsafe(_notify(), loop)
            threading.Thread(target=_record, daemon=True).start()

    async def _notify():
        cancel_event.set() 
        new_task.clear()
        new_task.set()

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    # --- The Core Execution Loop ---
    async with async_playwright() as p:
        # Puraana Brave browser connect karo
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        print("\nAgent ready!")
        print("Inputs accepted via CapsLock (Mic) OR WhatsApp (API)\n")

        async with aiohttp.ClientSession() as http_session:
            while True:
                await new_task.wait()
                new_task.clear()

                goal = pending["goal"]
                source = pending["source"]
                sender_id = pending["sender_id"]
                
                # Execution ke baad queue saaf karo
                pending["goal"] = None 

                if not goal:
                    continue

                if any(x in goal.lower() for x in ["band karo", "exit", "quit", "stop", "bye"]):
                    print("Band kar raha hoon...")
                    listener.stop()
                    break

                cancel_event.clear()  

                # Trigger the Digital Hitman
                final_answer = await run_agent(page, goal, cancel_event=cancel_event, session_history=session_history)

                if final_answer and not cancel_event.is_set():
                    session_history.append(f"User ({source}): {goal}")
                    session_history.append(f"Agent: {final_answer}")
                    
                    if len(session_history) > 8:
                        session_history = session_history[-8:]

                    # --- 4. The Snitch (Routing the Answer) ---
                    if source == "whatsapp" and sender_id:
                        print(f"Forwarding reply to WhatsApp ({sender_id})...")
                        try:
                            await http_session.post(
                                "http://localhost:3000/thing-reply",
                                json={"target_jid": sender_id, "text": final_answer}
                            )
                        except Exception as e:
                            print(f"Failed to send to Node.js: {e}")
                    else:
                        print(f"\nThing Says: {final_answer}")

                # Reset page state
                await page.evaluate('() => { window.__agentIdCounter = 0; }')
                print(f"\nReady for next command (Mic or WhatsApp)")

        print("\nShutting down...")
        await page.wait_for_timeout(2000)

if __name__ == "__main__":
    asyncio.run(main())