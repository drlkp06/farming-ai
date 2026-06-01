import json
import os

# ==========================================
# STATIC SEMANTIC GROUPS
# ==========================================

SEMANTIC_GROUPS = {

    "harvest_query": [

        "kitna nikla",
        "kitne nikle",
        "harvest quantity",
        "todai quantity",
        "tudai quantity",
        "kitna harvest hua",
        "aaj kitna nikla",

    ],

    "payment_query": [

        "kitna payment",
        "kitne rupye diye",
        "kitna diya",
        "abtak kitna gaya",
        "payment summary",
        "hisab",
        "hisaab",

    ],

    "treatment_query": [

        "last treatment",
        "latest treatment",
        "kya dala",
        "kab dala",
        "spray history",

    ]

}

# ==========================================
# SEMANTIC EQUIVALENTS
# ==========================================

SEMANTIC_EQUIVALENTS = {

    "nilka": "nikla",
    "niklaa": "nikla",

    "rupyee": "rupye",
    "rupees": "rupye",

    "todai": "harvest",
    "tudai": "harvest",

    "chhidkaav": "spray",
    "chhidkav": "spray",

}

# ==========================================
# MEMORY FILE
# ==========================================

DYNAMIC_GROUPS_FILE = (
    "memory/dynamic_semantic_groups.json"
)

# ==========================================
# LOAD DYNAMIC GROUPS
# ==========================================

def load_dynamic_semantic_groups():

    if not os.path.exists(
        DYNAMIC_GROUPS_FILE
    ):

        return {}

    try:

        with open(

            DYNAMIC_GROUPS_FILE,

            "r",

            encoding="utf-8"

        ) as f:

            return json.load(f)

    except Exception:

        return {}

# ==========================================
# SAVE DYNAMIC GROUPS
# ==========================================

def save_dynamic_semantic_groups(groups):

    os.makedirs(
        "memory",
        exist_ok=True
    )

    with open(

        DYNAMIC_GROUPS_FILE,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            groups,

            f,

            indent=2,

            ensure_ascii=False

        )
# ==========================================
# PHRASE ALIAS FILE
# ==========================================

PHRASE_ALIAS_FILE = (
    "memory/phrase_aliases.json"
)

# ==========================================
# LOAD PHRASE ALIASES
# ==========================================

def load_phrase_aliases():

    if not os.path.exists(
        PHRASE_ALIAS_FILE
    ):

        return {}

    try:

        with open(

            PHRASE_ALIAS_FILE,

            "r",

            encoding="utf-8"

        ) as f:

            return json.load(f)

    except Exception:

        return {}

# ==========================================
# SAVE PHRASE ALIASES
# ==========================================

def save_phrase_aliases(

    aliases

):

    os.makedirs(
        "memory",
        exist_ok=True
    )

    with open(

        PHRASE_ALIAS_FILE,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            aliases,

            f,

            indent=2,

            ensure_ascii=False

        )

# ==========================================
# TEACH PHRASE ALIAS
# ==========================================

def teach_phrase_alias(

    source,

    target

):

    aliases = load_phrase_aliases()

    source = source.lower().strip()

    target = target.lower().strip()

    aliases[source] = target

    save_phrase_aliases(
        aliases
    )

    return {

        "status":
        "learned",

        "source":
        source,

        "target":
        target

    }