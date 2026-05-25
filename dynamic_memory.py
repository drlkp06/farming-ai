import json
import os

DYNAMIC_KEYWORDS_FILE = "memory/dynamic_keywords.json"

def load_dynamic_keywords():
    if not os.path.exists(DYNAMIC_KEYWORDS_FILE):
        # Default empty structure
        return {"payment": [], "expense": [], "treatment": [], "harvest": []}
    
    with open(DYNAMIC_KEYWORDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_dynamic_keyword(operation, word):
    keywords = load_dynamic_keywords()
    if operation in keywords:
        if word not in keywords[operation]:
            keywords[operation].append(word)
    else:
        keywords[operation] = [word]
        
    with open(DYNAMIC_KEYWORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(keywords, f, indent=2)