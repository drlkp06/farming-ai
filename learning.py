import json
import os
import re

from semantic_engine import (
    build_semantic_state,
    learn_conversation_pattern
)
from semantic_knowledge import (
    teach_phrase_alias
)
from semantic_learning import (
    approve_candidate_learning
)
from context_engine import (
    get_pending_learning,
    set_pending_learning,
    clear_pending_learning
)
from dynamic_memory import save_dynamic_keyword
from context_engine import get_pending_learning, clear_pending_learning

def resolve_learning_confirmation(user_input):
    pending = get_pending_learning()
    if not pending:
        return None
        
    target_word = pending.get("target_word")
    user_response = user_input.lower().strip()
    
    if user_response == "skip" or user_response == "no":
        clear_pending_learning()
        return {"status": "rejected", "message": f"'{target_word}' ko skip kar diya."}
        
    valid_operations = ["payment", "expense", "treatment", "harvest", "crop", "product"]
    
    if user_response in valid_operations:
        # Save to memory dynamically
        save_dynamic_keyword(user_response, target_word)
        clear_pending_learning()
        return {
            "status": "confirmed", 
            "message": f"Done! Maine '{target_word}' ko '{user_response}' ke roop mein yaad kar liya hai."
        }
        
    return {"status": "invalid", "message": "Please valid type batao (expense/harvest/crop) ya 'skip' bolo."}
# ==========================================
# FILE PATH
# ==========================================

VOCAB_FILE = "memory/vocab.json"

# ==========================================
# LOAD VOCAB
# ==========================================

def load_vocab():

    if not os.path.exists(
        VOCAB_FILE
    ):

        return {}

    with open(

        VOCAB_FILE,

        "r",

        encoding="utf-8"

    ) as f:

        return json.load(f)

# ==========================================
# SAVE VOCAB
# ==========================================

def save_vocab(vocab):

    os.makedirs(
        "memory",
        exist_ok=True
    )

    with open(

        VOCAB_FILE,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            vocab,

            f,

            indent=2,

            ensure_ascii=False

        )

# ==========================================
# LEARN WORD
# ==========================================

def learn_word(

    word,

    data

):

    vocab = load_vocab()

    word = word.lower().strip()

    vocab[word] = data

    save_vocab(vocab)

    return {

        "status":
        "learned",

        "word":
        word

    }

# ==========================================
# GET WORD
# ==========================================

def get_word(word):

    vocab = load_vocab()

    return vocab.get(

        word.lower().strip(),

        None

    )

# ==========================================
# WORD EXISTS
# ==========================================

def word_exists(word):

    vocab = load_vocab()

    return (

        word.lower().strip()

        in

        vocab

    )

# ==========================================
# GET ALL WORDS
# ==========================================

def get_all_words():

    vocab = load_vocab()

    return list(

        vocab.keys()

    )

# ==========================================
# DELETE WORD
# ==========================================

def delete_word(word):

    vocab = load_vocab()

    word = word.lower().strip()

    if word in vocab:

        del vocab[word]

        save_vocab(vocab)

        return {

            "deleted":
            True,

            "word":
            word

        }

    return {

        "deleted":
        False,

        "word":
        word

    }

# ==========================================
# CHECK LEARNING COMMAND
# ==========================================

def is_learning_command(text):

    text = text.lower().strip()

    learning_prefixes = [

        "remember",
        "learn ",
        "train ",
        "teach "

    ]

    return any(

        text.startswith(prefix)

        for prefix in learning_prefixes

    )

# ==========================================
# CONFIRMATION CHECK
# ==========================================

def is_learning_confirmation(text):

    lowered = text.lower().strip()

    return lowered in [

        "yes",
        "y",
        "haan",
        "han",
        "haanji",
        "ok",
        "okay",
        "confirm",
        "approve",
        "save",
        "no",
        "n",
        "nahin",
        "na",
        "cancel",
        "skip",
        "reject"

    ]


def resolve_learning_confirmation(text):

    lowered = text.lower().strip()

    pending = get_pending_learning()

    if not pending:

        return {

            "status":
            "idle",

            "message":
            "No pending learning to confirm."

        }

    if lowered in [

        "no",
        "n",
        "nahin",
        "na",
        "cancel",
        "skip",
        "reject"

    ]:

        clear_pending_learning()

        return {

            "status":
            "rejected",

            "pending_learning":
            pending

        }

    pending["confirmed"] = True

    commit_result = learn_conversation_pattern(

        pending["raw_input"],

        pending["semantic_state"],

        auto_commit=True

    )

    approve_candidate_learning(
        pending.get("pattern")
    )

    clear_pending_learning()

    return {

        "status":
        "confirmed",

        "pending_learning":
        pending,

        "commit_result":
        commit_result

    }

# ==========================================
# PROCESS LEARNING COMMAND
# ==========================================

def process_learning_command(text):

    text = text.strip()

    # ==========================================
    # ALIAS LEARNING
    # ==========================================

    alias_match = re.match(

        r"^(?:learn|teach|train)\s+alias\s+(.+?)\s+(.+)$",

        text,

        re.IGNORECASE

    )

    if alias_match:

        return teach_phrase_alias(

            alias_match.group(1),

            alias_match.group(2)

        )

    # ==========================================
    # PHRASE LEARNING
    # ==========================================

    phrase_match = re.match(

        r"^(?:learn|teach|train)\s+phrase\s+(.+?)\s+means\s+(.+)$",

        text,

        re.IGNORECASE

    )

    if phrase_match:

        return teach_phrase_alias(

            phrase_match.group(1),

            phrase_match.group(2)

        )

    # ==========================================
    # GENERIC LEARNING
    # ==========================================

    parts = text.split(

        maxsplit=2

    )

    if len(parts) < 3:

        return {

            "status":
            "error",

            "message":

            (
                "Format: "
                "learn <intent> <sentence>"
            )

        }

    # ==========================================
    # EXTRACT
    # ==========================================

    intent = parts[1].lower()

    sentence = parts[2]

    # ==========================================
    # BUILD SEMANTIC STATE
    # ==========================================

    semantic_state = (

        build_semantic_state(

            sentence

        )

    )

    # ==========================================
    # FORCE LEARNED INTENT
    # ==========================================

    semantic_state[
        "intent"
    ] = intent

    # ==========================================
    # LEARN CONVERSATION PATTERN
    # ==========================================

    learn_result = (

        learn_conversation_pattern(

            sentence,

            semantic_state,

            auto_commit=True

        )

    )

    # ==========================================
    # RESPONSE
    # ==========================================

    return {

        "status":
        "learned",

        "intent":
        intent,

        "sentence":
        sentence,

        "semantic_learning":
        learn_result

    }

# ==========================================
# LEARN FROM SEMANTIC STATE (UPDATED)
# ==========================================

def learn_from_semantic_state(

    semantic_state

):

    if not semantic_state:

        return None

    raw_input = semantic_state.get(
        "raw_input"
    )

    if not raw_input:

        return None

    pending = get_pending_learning()

    if pending:

        return {

            "status":
            "pending_learning",

            "learning":
            pending

        }

    learn_result = learn_conversation_pattern(

        raw_input,

        semantic_state,

        auto_commit=False

    )

    # ---> ADDED FIX: Save to pending memory <---
    if learn_result:
        
        set_pending_learning({
            "raw_input": raw_input,
            "semantic_state": semantic_state,
            "pattern": learn_result.get("pattern")
        })

    return learn_result