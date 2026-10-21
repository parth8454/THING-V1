import json
import os
from datetime import datetime

MEMORY_FILE = "agent_memory.json"

def init_memory():
    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'w') as f:
            json.dump({"user_profile": {}, "knowledge_base": {}, "logs": []}, f, indent=4)

def save_to_memory(category, key, value):
    """
    Saves clean, summarized data to the memory bank.
    category: 'user_profile', 'knowledge_base', or 'logs'
    key: example, '2pac_info', 'favorite_food'
    value: The actual clean string/data to save.
    """
    with open(MEMORY_FILE, 'r') as f:
        memory = json.load(f)
        
    if category not in memory:
        memory[category] = {}
        
    memory[category][key] = {
        "data": value,
        "saved_at": str(datetime.now())
    }
    
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=4)
        
    return f"✅ Saved '{key}' to memory perfectly."

def read_memory(category, key=None):
    with open(MEMORY_FILE, 'r') as f:
        memory = json.load(f)
        
    if key:
        return memory.get(category, {}).get(key, "❌ Not found in memory.")
    return memory.get(category, "❌ Category empty.")