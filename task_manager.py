# ============================================================
# TASK MANAGER
# ============================================================

from embedding import create_embedding


# ============================================================
# CREATE TASK
# ============================================================

def create_task(ai_result, email):

    embedding_text = f"""
    Subject: {email["subject"]}
    Sender: {email["sender"]}

    Title: {ai_result["title"]}

    Action: {ai_result["action"]}

    Category: {ai_result["category"]}

    Priority: {ai_result["priority"]}

    Deadline: {ai_result["deadline"]}
    """

    embedding = create_embedding(
        embedding_text
    )


    task = {

        # ----------------------------------------------------
        # Email information
        # ----------------------------------------------------

        "message_id": email["message_id"],

        "sender": email["sender"],

        "subject": email["subject"],

        "date": email.get("date"),


        # ----------------------------------------------------
        # AI extracted information
        # ----------------------------------------------------

        "title": ai_result["title"],

        "action": ai_result["action"],

        "category": ai_result["category"],

        "action_required": ai_result["action_required"],

        "deadline": ai_result["deadline"],

        "priority": ai_result["priority"],


        # ----------------------------------------------------
        # Task status
        # ----------------------------------------------------

        "status": "pending",


        # ----------------------------------------------------
        # Calendar information
        # ----------------------------------------------------

        "event_required": ai_result.get(
            "event_required",
            False
        ),

        "event_title": ai_result.get(
            "event_title"
        ),

        "event_date": ai_result.get(
            "event_date"
        ),

        "event_start_time": ai_result.get(
            "event_start_time"
        ),

        "event_end_time": ai_result.get(
            "event_end_time"
        ),

        "event_location": ai_result.get(
            "event_location"
        ),

        "event_description": ai_result.get(
            "event_description"
        ),

        "event_timezone": ai_result.get("event_timezone"),

        # This will be filled after
        # Google Calendar creates the event.
        "calendar_event_id": None,


        # ----------------------------------------------------
        # Reply information
        # ----------------------------------------------------

        "reply_required": ai_result.get(
            "reply_required",
            False
        ),

        "reply_type": ai_result.get(
            "reply_type"
        ),

        "reply_recipient": ai_result.get(
            "reply_recipient"
        ),

        "reply_subject": ai_result.get(
            "reply_subject"
        ),

        "ai_explanation": ai_result.get(
            "ai_explanation"
        ),


        # ----------------------------------------------------
        # Embedding
        # ----------------------------------------------------

        "embedding": embedding
    }


    return task