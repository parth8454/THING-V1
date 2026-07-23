import os
from groq import AsyncGroq

os.environ["GROQ_API_KEY"] = "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"

MODELS = ["openai/gpt-oss-120b","llama-3.1-8b-instant","llama-3.3-70b-versatile","openai/gpt-oss-20b"]

TEXT_MODEL = MODELS[3]

VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

UI_NOISE_BLACKLIST = ["close", "dismiss", "cookie"]

client = AsyncGroq()
