import json

from extractor import (
    process_input
)

from response_engine import (
    format_response
)

from entity_memory import (
    initialize_entity_database
)

from event_memory import (
    initialize_event_database
)

from product_memory import (
    initialize_product_database
)

# ==========================================
# SYSTEM START
# ==========================================

initialize_entity_database()

initialize_product_database()

initialize_event_database()

print(
    "Farming AI Assistant Started"
)

print(
    "Type 'exit' to quit"
)

# ==========================================
# MAIN LOOP
# ==========================================

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

    # ==========================================
    # NORMALIZE
    # ==========================================

    user_input = user_input.strip()

    # ==========================================
    # EMPTY INPUT
    # ==========================================

    if not user_input:

        continue

    # ==========================================
    # EXIT
    # ==========================================

    if (

        user_input.lower()

        ==

        "exit"

    ):

        print(
            "Goodbye!"
        )

        break

    # ==========================================
    # PROCESS INPUT
    # ==========================================

    semantic_states = process_input(

        user_input

    )

    # ==========================================
    # SAFETY
    # ==========================================

    if semantic_states is None:

        print(

            format_response(
                None
            )

        )

        continue

    # ==========================================
    # PRINT RESPONSES
    # ==========================================

    for semantic_state in semantic_states:

        print(

            format_response(
                semantic_state
            )

        )
