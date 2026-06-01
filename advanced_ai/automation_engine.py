from datetime import (

    datetime,

    timedelta

)

AUTOMATIONS = []

# ==========================================
# CREATE AUTOMATION
# ==========================================

def create_automation(

    automation_type,

    title,

    trigger_date,

    metadata=None

):

    automation = {

        "id":

        len(AUTOMATIONS) + 1,

        "type":

        automation_type,

        "title":

        title,

        "trigger_date":

        trigger_date,

        "metadata":

        metadata or {},

        "status":

        "active"

    }

    AUTOMATIONS.append(
        automation
    )

    return automation

# ==========================================
# TREATMENT FOLLOWUP
# ==========================================

def create_treatment_followup(

    crop,

    product,

    treatment_type=None,

    application_method=None,

    days=5

):

    trigger_date = (

        datetime.now()

        +

        timedelta(days=days)

    )

    return create_automation(

        automation_type="treatment_followup",

        title=

        f"Check {crop} after "

        f"{product} treatment",

        trigger_date=

        trigger_date.strftime(
            "%Y-%m-%d"
        ),

        metadata={

            "crop": crop,

            "product": product,

            "treatment_type": treatment_type,

            "application_method": application_method

        }

    )
# ==========================================
# PEST MONITORING
# ==========================================

def create_pest_monitoring(

    crop,

    pest,

    days=3

):

    trigger_date = (

        datetime.now()

        +

        timedelta(days=days)

    )

    return create_automation(

        automation_type="pest_monitoring",

        title=

        f"Monitor {pest} in {crop}",

        trigger_date=

        trigger_date.strftime(
            "%Y-%m-%d"
        ),

        metadata={

            "crop": crop,

            "pest": pest

        }

    )

# ==========================================
# GET ACTIVE AUTOMATIONS
# ==========================================

def get_active_automations():

    return [

        item

        for item in AUTOMATIONS

        if item["status"] == "active"

    ]

# ==========================================
# COMPLETE AUTOMATION
# ==========================================

def complete_automation(

    automation_id

):

    for item in AUTOMATIONS:

        if item["id"] == automation_id:

            item["status"] = "completed"

            return {

                "completed": True,

                "automation_id":

                automation_id

            }

    return {

        "completed": False

    }

# ==========================================
# GET DUE AUTOMATIONS
# ==========================================

def get_due_automations():

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    due = []

    for item in AUTOMATIONS:

        if (

            item["status"] == "active"

            and

            item["trigger_date"] <= today

        ):

            due.append(item)

    return due

# ==========================================
# AUTO ACTION FROM EVENT
# ==========================================

def auto_plan_from_event(data):

    operation = data.get(
        "operation"
    )

    crop = data.get(
        "crop"
    )

    product = data.get(
        "product"
    )

    pest = data.get(
        "pest"
    )

    created = []

    # ==========================================
    # TREATMENT FOLLOWUP
    # ==========================================

    if (

        operation == "treatment"

        and crop

        and product

    ):

        followup = create_treatment_followup(

            crop,

            product,

            treatment_type=data.get(
                "treatment_type"
            ),

            application_method=data.get(
                "application_method"
            )

        )

        created.append(
            followup
        )

    # ==========================================
    # PEST MONITORING
    # ==========================================

    if pest and crop:

        monitoring = create_pest_monitoring(

            crop,

            pest

        )

        created.append(
            monitoring
        )

    return created

# ==========================================
# DAILY AUTOMATION SUMMARY
# ==========================================

def automation_summary():

    active = get_active_automations()

    due = get_due_automations()

    return {

        "active_automations":

        len(active),

        "due_today":

        len(due),

        "due_items":

        due

    }