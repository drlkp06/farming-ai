print(
    "\n[ENTITY ENGINE LOADED]"
)
import re
from memory_system.entity_memory import (
    load_entities,
    save_entity
)

# ==========================================
# GET LEARNED WORKER
# ==========================================

def get_learned_worker(words):

    workers = load_entities(
        "worker"
    )

    for word in words:

        word = word.lower()

        if word in workers:

            return word

    return None

# ==========================================
# GET LEARNED CROP
# ==========================================

def get_learned_crop(words):

    crops = load_entities(
        "crop"
    )

    for word in words:

        word = word.lower()

        if word in crops:

            return word

    return None

# ==========================================
# GET LEARNED PRODUCT
# ==========================================

def get_learned_product(words):

    products = load_entities(
        "product"
    )

    for word in words:

        word = word.lower()

        if word in products:

            return word

    return None

# ==========================================
# ALL ENTITIES
# ==========================================

def get_all_entities():

    return load_entities()

# ==========================================
# UNKNOWN ENTITY DETECTION
# ==========================================

def detect_unknown_entities(

    user_input,

    semantic_data

):
    print(
        "\n[ENTITY DEBUG] DETECTOR RUNNING"

    )
    words = user_input.lower().split()

    all_entities = load_entities()

    ignore_words = [

        # grammar
        "ko",
        "ka",
        "ke",
        "ki",
        "hai",
        "me",
        "par",
        "se",

        # numbers/payment
        "rupye",
        "rupyee",
        "diye",
        "kitna",
        "kitne",
        "abtak",
        "milaake",
        "milake",
        "milakar",
        "mila",
        "gaya",
        "gya",
        "total",
        "summary",

        # bookkeeping
        "pura",
        "poora",
        "lekha",
        "jokha",
        "khata",
        "cash",
        "book",

        # conversational
        "dikhao",
        "batao",
        "aaj",
        "abhi",
        "tak",

        # treatment operations
        "spray",
        "fertilizer",
        "treatment",
        "drip",
        "drenching",
        "dressing",
        "fertigation",

        # harvest
        "harvest",
        "tudai",
        "maal",
        "output",
        "production",

        # misc
        "kiya",
        "diya"

    ]

    # ==========================================
    # FERTILIZER GRADE PATTERN
    # ==========================================

    fertilizer_pattern = r"\d{1,2}[.:]\d{1,2}[.:]\d{1,2}"

    for word in words:

        clean_word = word.strip().lower()

        # ==========================================
        # SKIP NON-ALPHA
        # ==========================================

        if not clean_word.replace(":", "").replace(".", "").isalnum():

            continue

        # ==========================================
        # SKIP FERTILIZER GRADE
        # ==========================================

        if re.fullmatch(
            fertilizer_pattern,
            clean_word
        ):

            continue

        # ==========================================
        # SKIP KNOWN / IGNORE
        # ==========================================

        if (

            clean_word in all_entities

            or clean_word in ignore_words

        ):

            continue

        print(

            f"\nAI : '{clean_word}' ka role kya hai?\n"

            f"(worker/vendor/buyer/machine/crop/product/skip)"

        )

        role = input(
            "\nYou : "
        ).lower().strip()

        allowed_roles = [

            "worker",
            "vendor",
            "buyer",
            "machine",
            "crop",
            "product",
            "skip"

        ]

        if role not in allowed_roles:

            print(

                "\nAI : Invalid entity type."

            )

            return True

        if role == "skip":

            return False

        save_entity(

            clean_word,

            role

        )

        print(

            f"\nAI : "

            f"{clean_word} ko "

            f"{role} ke roop me "

            f"learn kar liya."

        )
        # ==========================================
        # UPDATE CURRENT RECORD
        # ==========================================

        if role == "worker":

            semantic_data["worker"] = word

            semantic_data["person"] = word

        elif role == "crop":

            semantic_data["crop"] = word

        elif role == "product":

            semantic_data["product"] = word

        elif role == "vendor":

            semantic_data["vendor"] = word

        elif role == "buyer":

            semantic_data["buyer"] = word

        return False
