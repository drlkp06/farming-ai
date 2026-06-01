import json

# ==========================================
# DEBUG MODE
# ==========================================

DEBUG_MODE = True

# ==========================================
# FORMAT RESPONSE
# ==========================================

def format_response(

    semantic_state

):

    # ==========================================
    # EMPTY RESULT
    # ==========================================

    if semantic_state is None:

        return (

            "\nAI : "
            "Sorry, I could not understand."

        )

    lines = []

    # ==========================================
    # DEBUG OUTPUT
    # ==========================================

    if DEBUG_MODE:

        lines.append(

            "\nSemantic State :\n"

        )

        lines.append(

            json.dumps(

                semantic_state,

                indent=2,

                ensure_ascii=False,

                default=str

            )

        )

    # ==========================================
    # QUERY RESULT
    # ==========================================

    query_result = semantic_state.get(

        "query_result"

    )

    # ==========================================
    # SAVE STATUS
    # ==========================================

    save_status = semantic_state.get(

        "save_status"

    )

    if save_status is None:

        save_status = {}

    # ==========================================
    # ENTRY RESPONSE
    # ==========================================

    if semantic_state.get(

        "is_entry"

    ):

        # ==========================================
        # SUCCESS
        # ==========================================

        if save_status.get(

            "saved"

        ):

            lines.append(

                "\nRecord saved."

            )

        # ==========================================
        # DUPLICATE
        # ==========================================

        elif (

            save_status.get(
                "reason"
            )

            ==

            "duplicate_event"

        ):

            lines.append(

                "\nDuplicate entry ignored."

            )

        # ==========================================
        # SAVE FAILED
        # ==========================================

        else:

            lines.append(

                "\nRecord not saved."

            )

    # ==========================================
    # QUERY RESPONSE
    # ==========================================

    elif semantic_state.get(

        "is_query"

    ):

        if not query_result:

            lines.append(

                "\nAI : No query result found."

            )

        else:

            query_type = query_result.get(
                "query_type"
            )

            message = query_result.get(
                "message"
            )

            if message:

                lines.append(

                    f"\n{message}"

                )

            # ==========================================
            # TOTAL PAYMENT
            # ==========================================

            elif query_type == "total_payment":

                formatted = query_result.get(

                    "formatted"

                )

                if formatted:

                    lines.append(

                        f"\nAI : {formatted}"

                    )

                else:

                    total = query_result.get(

                        "total_payment",

                        0

                    )

                    lines.append(

                        f"\nAI : {total} Rs"

                    )

            # ==========================================
            # PAYMENT HISTORY
            # ==========================================

            elif query_type == "payment_history":

                history = query_result.get(
                    "history",
                    []
                )

                if not history:

                    lines.append(

                        "\nAI : No payment history found."

                    )

                else:

                    lines.append(

                        "\nAI : Payment History :"

                    )

                    for row in history:

                        if len(row) >= 3:

                            worker = row[0]
                            amount = row[1]
                            date = row[2]

                            lines.append(

                                f"- {worker}: {amount} "
                                f"on {date}"

                            )

                            continue

                        amount = row[0]
                        date = row[1]

                        lines.append(

                            f"- {amount} "
                            f"on {date}"

                        )

            # ==========================================
            # TOTAL EXPENSE
            # ==========================================

            elif query_type == "total_expense":

                formatted = query_result.get(

                    "formatted"

                )

                if formatted:

                    lines.append(

                        f"\nAI : {formatted}"

                    )

                else:

                    total = query_result.get(

                        "total_expense",

                        0

                    )

                    lines.append(

                        f"\nAI : {total} Rs"

                    )

# ==========================================
# HARVEST QUANTITY
# ==========================================

            elif query_type == "harvest_quantity":

                formatted = query_result.get(

                    "formatted"

                )

                if formatted:

                    lines.append(

                        f"\nAI : {formatted}"

                    )

                else:

                    total = query_result.get(

                        "total_harvest",

                        0

                    )

                    lines.append(

                        f"\nAI : {total} kg"

                    )
            # ==========================================
            # LAST TREATMENT
            # ==========================================

            elif query_type == "last_treatment":

                treatment = query_result.get(
                    "treatment"
                )

                if not treatment:

                    lines.append(

                        "\nAI : No treatment found."

                    )

                else:

                    lines.append(

                        f"\nLast treatment : "
                        f"{treatment}"

                    )

            # ==========================================
            # PRODUCT HISTORY
            # ==========================================

            elif query_type == "product_history":

                history = query_result.get(
                    "history",
                    []
                )

                if not history:

                    lines.append(

                        "\nNo product history found."

                    )

                else:

                    lines.append(

                        "\nAI : Product History :"

                    )

                    for row in history:

                        lines.append(

                            f"- {row}"

                        )

            # ==========================================
            # UNKNOWN QUERY
            # ==========================================

            else:

                lines.append(

                    "\nAI : SQuery executed."

                )

    # ==========================================
    # CLARIFICATION
    # ==========================================

    if semantic_state.get(

        "needs_clarification"

    ):

        missing_fields = semantic_state.get(

            "missing_fields",

            []

        )

        if missing_fields:

            field = missing_fields[0]

            lines.append(

                f"\nAI : "
                f"Please provide {field}."

            )

    # ==========================================
    # LEARNING SUGGESTION
    # ==========================================

    learning_suggestion = semantic_state.get(
        "learning_suggestion"
    )

    # ==========================================
    # SHOW ONLY REAL PENDING LEARNING
    # ==========================================

    if (

        learning_suggestion

        and

        learning_suggestion.get(
            "status"
        ) not in [

            "already_known",
            "learned_pattern"

        ]

    ):

        message = learning_suggestion.get(
            "message"
        )

        if message:

            lines.append(

                f"\nAI : {message}"

            )

        else:

            lines.append(

                "\nAI : "
                "Naya pattern mila hai. "
                "Yes bolkar save karo, no bolkar skip."

            )

       # ==========================================
    # LEARNING CONFIRMATION
    # ==========================================

    learning_confirmation = semantic_state.get(
        "learning_confirmation"
    )

    if learning_confirmation:

        status = learning_confirmation.get(
            "status"
        )

        # ==========================================
        # CONFIRMED
        # ==========================================

        if (

            status == "confirmed"

            and

            learning_confirmation.get(
                "commit_result"
                )

                or

                {}
            ).get(
                "approved",
                True
            ):
            

            lines.append(

                "\nLearning saved."

            )

        # ==========================================
        # REJECTED
        # ==========================================

        elif status == "rejected":

            lines.append(

                "\nAI : Learning skipped."

            )

        # ==========================================
        # NO PENDING
        # ==========================================

        elif status in [

                "no_pending",
                "idle"

        ]:

            lines.append(

                "\nAI : No pending learning to confirm."

            )

        # ==========================================
        # CUSTOM MESSAGE
        # ==========================================

        else:

            message = learning_confirmation.get(
                "message"
            )

            if message:

                lines.append(

                    f"\nAI : {message}"

                )

            else:

                lines.append(

                    "AI : Learning state updated."

                )
    # ==========================================
    # FINAL OUTPUT
    # ==========================================

    return "\n".join(lines)
