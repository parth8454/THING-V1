import os

# ─── GITHUB CONFIG (DUMMY TOKEN) ───────────────────────────
GITHUB_TOKEN = "ghp_your_dummy_github_token_here"
os.environ["GITHUB_TOKEN"] = GITHUB_TOKEN   

# ─── PROVIDER CONFIG ───────────────────────────────────────
# Change PROVIDER to switch models:
# "groq"      → free, fast
# "openai"    → GPT-4o, GPT-4 etc
# "anthropic" → Claude models
# "gemini"    → Gemini models

MODELS_LIST = ["groq", "openai", "anthropic", "gemini"]

PROVIDER = MODELS_LIST[0]  # Change this to switch providers

# ─── MODEL NAMES ───────────────────────────────────────────
MODELS = {
    "groq": {
        "text": "openai/gpt-oss-120b",
        "vision": "meta-llama/llama-4-scout-17b-16e-instruct"
    },
    "openai": {
        "text": "gpt-4o",
        "vision": "gpt-4o"
    },
    "anthropic": {
        "text": "claude-sonnet-4-6",
        "vision": "claude-sonnet-4-6"
    },
    "gemini": {
        "text": "Gemini 3 Flash",
        "vision": "gemini-2.0-flash"
    }
}   

TEXT_MODEL = MODELS[PROVIDER]["text"]
VISION_MODEL = MODELS[PROVIDER]["vision"]

UI_NOISE_BLACKLIST = ["close", "dismiss", "cookie"]

# ─── CLIENT SETUP (DUMMY API KEYS) ─────────────────────────
if PROVIDER == "groq":
    from groq import AsyncGroq
    os.environ["GROQ_API_KEY"] = "gsk_your_dummy_groq_api_key_here"
    client = AsyncGroq()

elif PROVIDER == "openai":
    from openai import AsyncOpenAI
    os.environ["OPENAI_API_KEY"] = "sk-your_dummy_openai_api_key_here"
    client = AsyncOpenAI()

elif PROVIDER == "anthropic":
    from anthropic import AsyncAnthropic
    os.environ["ANTHROPIC_API_KEY"] = "sk-ant-your_dummy_anthropic_api_key_here"
    client = AsyncAnthropic()  

elif PROVIDER == "gemini":
    from google import genai
    os.environ["GEMINI_API_KEY"] = "AIza_your_dummy_gemini_api_key_here"
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])