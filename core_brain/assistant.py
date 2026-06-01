import traceback

from core_brain.extractor import (
    process_input
)

from core_brain.response_engine import (
    format_response
)

# ==========================================
# MEMORY INITIALIZATION
# ==========================================

from memory_system.entity_memory import (
    initialize_entity_database
)

from memory_system.event_memory import (
    initialize_event_database
)

from memory_system.product_memory import (
    initialize_product_database
)

from memory_system.dynamic_memory import (
    initialize_memory_database
)

# ==========================================
# DEBUG CONFIG
# ==========================================

DEBUG_MODE = True

# ==========================================
# BOOTSTRAP COGNITION SYSTEM
# ==========================================

def initialize_cognition_system():

    initialize_entity_database()

    initialize_product_database()

    initialize_event_database()

    initialize_memory_database()

# ==========================================
# STARTUP BANNER
# ==========================================

def print_startup_banner():

    print(
        "\n=================================="
    )

    print(
        "Adaptive Farming AI Started"
    )

    print(
        "Semantic Cognition Engine Online"
    )

    print(
        "Type 'exit' to quit"
    )

    print(
        "=================================="
    )

# ==========================================
# SAFE RESPONSE PRINT
# ==========================================

def print_response(

    semantic_state

):

    try:

        print(

            format_response(
                semantic_state
            )

        )

    except Exception as e:

        print(

            "\n[Response Error]",

            str(e)

        )

        if DEBUG_MODE:

            traceback.print_exc()

# ==========================================
# SAFE INPUT PROCESSING
# ==========================================

def process_user_input(

    user_input

):

    try:

        semantic_states = process_input(
            user_input
        )

        if semantic_states is None:

            print_response(
                None
            )

            return

        for semantic_state in semantic_states:

            print_response(
                semantic_state
            )

    except Exception as e:

        print(

            "\n[System Error]",

            str(e)

        )

        if DEBUG_MODE:

            traceback.print_exc()

# ==========================================
# MAIN LOOP
# ==========================================

def run_assistant():

    initialize_cognition_system()

    print_startup_banner()

    while True:

        try:

            user_input = input(
                "\nYou : "
            )

        except KeyboardInterrupt:

            print(
                "\nGoodbye!"
            )

            break

        except EOFError:

            print(
                "\nSession closed."
            )

            break

        # ==========================================
        # NORMALIZATION
        # ==========================================

        user_input = (
            user_input
            .strip()
        )

        # ==========================================
        # EMPTY INPUT
        # ==========================================

        if not user_input:

            continue

        # ==========================================
        # EXIT
        # ==========================================

        if user_input.lower() == "exit":

            print(
                "Goodbye!"
            )

            break

        # ==========================================
        # PROCESS
        # ==========================================

        process_user_input(
            user_input
        )

# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":

    run_assistant()