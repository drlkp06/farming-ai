import json
import os
from datetime import datetime

# ==========================================
# DYNAMIC MEMORY FILE
# ==========================================

DYNAMIC_KEYWORDS_FILE = (
    "config_memory/dynamic_keywords.json"
)

# ==========================================
# DEFAULT STRUCTURE
# ==========================================

DEFAULT_DYNAMIC_KEYWORDS = {

    "payment": [],
    "expense": [],
    "treatment": [],
    "harvest": [],
    "pest_attack": []

}
# ==========================================
# FUNCTIONAL LANGUAGE MEMORY FILE
# ==========================================

FUNCTIONAL_LANGUAGE_FILE = (

    "memory/"
    "functional_language.json"

)

# ==========================================
# LOAD FUNCTIONAL LANGUAGE
# ==========================================

def load_functional_language():

    if not os.path.exists(

        FUNCTIONAL_LANGUAGE_FILE

    ):

        return {}

    with open(

        FUNCTIONAL_LANGUAGE_FILE,

        "r",

        encoding="utf-8"

    ) as f:

        return json.load(f)
    
# ==========================================
# SAVE FUNCTIONAL LANGUAGE
# ==========================================

def save_functional_language(

    word,
    role

):

    memory = load_functional_language()

    memory[word] = role

    with open(

        FUNCTIONAL_LANGUAGE_FILE,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            memory,
            f,
            indent=2,
            ensure_ascii=False

        )
# ==========================================
# INITIALIZE MEMORY
# ==========================================

def initialize_memory_database():

    os.makedirs(

        os.path.dirname(
            DYNAMIC_KEYWORDS_FILE
        ),

        exist_ok=True

    )

    if not os.path.exists(
        DYNAMIC_KEYWORDS_FILE
    ):

        with open(

            DYNAMIC_KEYWORDS_FILE,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                DEFAULT_DYNAMIC_KEYWORDS,

                f,

                indent=2,

                ensure_ascii=False

            )

# ==========================================
# LOAD DYNAMIC KEYWORDS
# ==========================================

def load_dynamic_keywords():

    initialize_memory_database()

    try:

        with open(

            DYNAMIC_KEYWORDS_FILE,

            "r",

            encoding="utf-8"

        ) as f:

            data = json.load(f)

    except Exception:

        return DEFAULT_DYNAMIC_KEYWORDS.copy()

    # ==========================================
    # ENSURE REQUIRED GROUPS
    # ==========================================

    for key, value in DEFAULT_DYNAMIC_KEYWORDS.items():

        data.setdefault(
            key,
            value
        )

    return data

# ==========================================
# SAVE DYNAMIC KEYWORD
# ==========================================

def save_dynamic_keyword(

    operation,

    word,

    confidence=0.55

):

    if not operation:

        return False

    if not word:

        return False

    operation = (
        operation
        .strip()
        .lower()
    )

    word = (
        word
        .strip()
        .lower()
    )

    if not word:

        return False

    keywords = load_dynamic_keywords()

    keywords.setdefault(
        operation,
        []
    )

    # ==========================================
    # NORMALIZED DUPLICATE CHECK
    # ==========================================

    existing_words = {

        item["word"]

        if isinstance(item, dict)

        else item

        for item in keywords[operation]

    }

    if word in existing_words:

        return False

    # ==========================================
    # SAVE STRUCTURED MEMORY
    # ==========================================

    keywords[operation].append({

        "word":
        word,

        "confidence":
        round(confidence, 2),

        "learned_at":
        datetime.now().isoformat()

    })

    # ==========================================
    # SORT MEMORY
    # ==========================================

    keywords[operation] = sorted(

        keywords[operation],

        key=lambda x: x["word"]

    )

    with open(

        DYNAMIC_KEYWORDS_FILE,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            keywords,

            f,

            indent=2,

            ensure_ascii=False

        )

    return True

# ==========================================
# GET WORDS ONLY
# ==========================================

def get_dynamic_words(

    operation

):

    keywords = load_dynamic_keywords()

    return [

        item["word"]

        if isinstance(item, dict)

        else item

        for item in keywords.get(
            operation,
            []
        )

    ]

# ==========================================
# AUTO INITIALIZE
# ==========================================

initialize_memory_database()