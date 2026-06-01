import json
import os
import re
from difflib import SequenceMatcher

from knowledge_learning.semantic_knowledge import (

    SEMANTIC_GROUPS,
    SEMANTIC_EQUIVALENTS,
    load_dynamic_semantic_groups,
    save_dynamic_semantic_groups

)

# ==========================================
# MEMORY FILE
# ==========================================

CANDIDATE_MEMORY_FILE = (
    "config_memory/candidate_rules.json"
)

# ==========================================
# LOAD MEMORY
# ==========================================

def load_candidate_memory():

    if not os.path.exists(
        CANDIDATE_MEMORY_FILE
    ):

        return {
            "candidate_rules": []
        }

    try:

        with open(

            CANDIDATE_MEMORY_FILE,

            "r",

            encoding="utf-8"

        ) as f:

            return json.load(f)

    except Exception:

        return {
            "candidate_rules": []
        }


def _candidate_records(memory):

    if isinstance(
        memory,
        dict
    ):

        return memory.setdefault(
            "candidate_rules",
            []
        )

    if isinstance(
        memory,
        list
    ):

        return memory

    return []

# ==========================================
# SAVE MEMORY
# ==========================================

def save_candidate_memory(memory):

    os.makedirs(

        os.path.dirname(
            CANDIDATE_MEMORY_FILE
        ),

        exist_ok=True

    )

    with open(

        CANDIDATE_MEMORY_FILE,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            memory,

            f,

            indent=2,

            ensure_ascii=False

        )


def store_candidate_learning(candidate):

    memory = load_candidate_memory()

    records = _candidate_records(
        memory
    )

    candidate_phrase = (
        candidate.get("candidate_phrase")
        or candidate.get("pattern")
        or candidate.get("phrase")
    )

    if not candidate_phrase:

        return None

    record = {

        "candidate_phrase":
        candidate_phrase,

        "possible_group":
        candidate.get("possible_group")
        or candidate.get("intent")
        or "semantic_pattern",

        "matched_signal":
        candidate.get("matched_signal")
        or "semantic_pattern",

        "confidence":
        round(
            float(candidate.get("confidence", 0.55)),
            2
        ),

        "example_text":
        candidate.get("example_text")
        or candidate.get("raw_input")
        or "",

        "status":
        "pending",

        "times_observed":
        int(candidate.get("times_observed", 1)),

        "created_at":
        candidate.get("created_at")
        or candidate.get("timestamp")
        or ""

    }

    records.append(

        record

    )

    save_candidate_memory(

        memory

    )

    return record


def approve_candidate_learning(candidate_phrase):

    memory = load_candidate_memory()

    records = _candidate_records(
        memory
    )

    updated = None

    for item in records:

        if item.get("candidate_phrase") != candidate_phrase:

            continue

        item["status"] = "approved"

        item["approved"] = True

        updated = item

    save_candidate_memory(

        memory

    )

    return updated

# ==========================================
# DETECT CANDIDATE RULE
# ==========================================

def detect_candidate_rule(

    user_input,

    intent_abstraction

):

    normalized = (

        user_input
        .lower()
        .strip()
    )

    normalized = " ".join(
        normalized.split()
    )

    best_group = None

    best_score = 0.0

    # ==========================================
    # STATIC GROUPS
    # ==========================================

    all_groups = dict(
        SEMANTIC_GROUPS
    )

    # ==========================================
    # DYNAMIC GROUPS
    # ==========================================

    dynamic_groups = (
        load_dynamic_semantic_groups()
    )

    all_groups.update(
        dynamic_groups
    )

    # ==========================================
    # SEMANTIC MATCH
    # ==========================================

    for group_name, phrases in all_groups.items():

        for phrase in phrases:

            similarity = SequenceMatcher(

                None,

                normalized,

                phrase.lower()

            ).ratio()

            if similarity > best_score:

                best_group = group_name

                best_score = similarity

    # ==========================================
    # THRESHOLD
    # ==========================================

    if best_score < 0.72:

        return None

    # ==========================================
    # ALREADY EXISTS
    # ==========================================

    memory = load_candidate_memory()

    records = _candidate_records(
        memory
    )

    for item in records:

        if item.get(
            "candidate_phrase"
        ) == normalized:

            return None

  # ==========================================
    # GENERALIZE NUMBERS
    # ==========================================

    generalized_pattern = re.sub(

        r"\b\d+(?:\.\d+)?\b",

        "<number>",

        normalized

    )


    # ==========================================
    # CREATE CANDIDATE
    # ==========================================

    candidate = {

        "kind":
        "semantic_pattern",

        "pattern":
        generalized_pattern,

        "candidate_phrase":
        generalized_pattern,

        "possible_group":
        best_group,

        "mode":
        "entry",

        "confidence":
        round(best_score, 2),

        "approved":
        False

    }

    records.append(
        candidate
    )

    save_candidate_memory(
        memory
    )

    return candidate

# ==========================================
# APPROVE RULE
# ==========================================

def approve_candidate_rule(

    candidate_phrase

):

    candidate_phrase = (

        candidate_phrase
        .lower()
        .strip()

    )

    memory = load_candidate_memory()

    records = _candidate_records(
        memory
    )

    dynamic_groups = (
        load_dynamic_semantic_groups()
    )

    approved = False

    approved_group = None

    for item in records:

        stored_phrase = (

            item.get(
                "candidate_phrase",
                ""
            )

            .lower()
            .strip()

        )

        if stored_phrase != candidate_phrase:

            continue

        group = item.get(
            "possible_group"
        )

        if not group:

            continue

        dynamic_groups.setdefault(
            group,
            []
        )

        if candidate_phrase not in dynamic_groups[group]:

            dynamic_groups[group].append(
                candidate_phrase
            )

        item["approved"] = True

        item["status"] = "approved"

        approved = True

        approved_group = group

    save_dynamic_semantic_groups(
        dynamic_groups
    )

    save_candidate_memory(
        memory
    )

    return {

        "approved":
        approved,

        "phrase":
        candidate_phrase,

        "group":
        approved_group

    }

# ==========================================
# GET PENDING RULES
# ==========================================

def get_pending_candidate_rules():

    memory = load_candidate_memory()

    records = _candidate_records(
        memory
    )

    return [

        item

        for item in records

        if not item.get(
            "approved"
        )

    ]
