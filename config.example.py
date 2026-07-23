import os
from groq import AsyncGroq

os.environ["GROQ_API_KEY"] = "your-api-key-here"

MODELS = ["llama-3.3-70b-versatile"]

TEXT_MODEL = MODELS[0]

VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

UI_NOISE_BLACKLIST = ["close", "dismiss", "cookie"]

client = AsyncGroq()