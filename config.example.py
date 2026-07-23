import os
from groq import AsyncGroq

os.environ["GROQ_API_KEY"] = "your-api-key-here"

# guys tool calling is not reliable on "llama-3.3-70b-versatile" it often fails and its a problem 
# from model's end hence dont waste time fixing this, thankyou!

MODELS = ["openai/gpt-oss-120b","llama-3.1-8b-instant","llama-3.3-70b-versatile","openai/gpt-oss-20b"]

VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

UI_NOISE_BLACKLIST = ["close", "dismiss", "cookie"]

client = AsyncGroq()
