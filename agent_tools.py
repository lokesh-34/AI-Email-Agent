# ============================================================
# IMPORTS
# ============================================================

from database import (
    get_pending_tasks,
    update_task_status,
    get_upcoming_tasks,
    get_completed_tasks,
    semantic_search_tasks,
    hybrid_search_tasks,
    get_all_drafts,
    get_draft_by_id
)

from gmail_reader import (
    connect_gmail,
    get_email_for_agent
)

from google_calendar import (
    get_upcoming_calendar_events
)


# ============================================================
# CLEAN TASK
# ============================================================
# MongoDB documents contain a 384-dimensional embedding.
# We NEVER want to send that embedding to the LLM.
#
# This function keeps only the information the agent needs.
# ============================================================

def clean_task(task):

    return {

        "message_id": task.get(
            "message_id"
        ),

        "sender": task.get(
            "sender"
        ),

        "subject": task.get(
            "subject"
        ),

        "title": task.get(
            "title"
        ),

        "action": task.get(
            "action"
        ),

        "category": task.get(
            "category"
        ),

        "action_required": task.get(
            "action_required"
        ),

        "deadline": task.get(
            "deadline"
        ),

        "priority": task.get(
            "priority"
        ),

        "status": task.get(
            "status"
        ),

        "reply_required": task.get(
            "reply_required"
        )
    }


# ============================================================
# GET PENDING TASKS
# ============================================================

def get_pending_tasks_tool():

    tasks = get_pending_tasks()

    return [
        clean_task(task)
        for task in tasks
    ]


# ============================================================
# COMPLETE TASK
# ============================================================

def complete_task_tool(message_id):

    result = update_task_status(
        message_id,
        "completed"
    )

    return {
        "message_id": message_id,
        "updated": result > 0,
        "status": "completed"
    }


# ============================================================
# FIND TASK
# ============================================================

def find_task_tool(search_text):

    tasks = get_pending_tasks()

    matches = []

    search_text = search_text.lower().strip()


    # ========================================================
    # EXACT / PHRASE SEARCH
    # ========================================================

    for task in tasks:

        fields = [

            task.get(
                "title",
                ""
            ),

            task.get(
                "action",
                ""
            ),

            task.get(
                "subject",
                ""
            ),

            task.get(
                "sender",
                ""
            ),

            task.get(
                "category",
                ""
            )
        ]

        fields = [
            str(field).lower()
            for field in fields
        ]

        if any(
            search_text in field
            for field in fields
        ):

            matches.append(
                clean_task(task)
            )


    # If exact/phrase matches exist,
    # return them immediately.

    if matches:

        return matches


    # ========================================================
    # KEYWORD SEARCH
    # ========================================================

    keywords = search_text.split()


    for task in tasks:

        fields = [

            task.get(
                "title",
                ""
            ),

            task.get(
                "action",
                ""
            ),

            task.get(
                "subject",
                ""
            ),

            task.get(
                "sender",
                ""
            ),

            task.get(
                "category",
                ""
            )
        ]

        combined_text = " ".join(
            str(field)
            for field in fields
        ).lower()


        matched_keywords = 0


        for keyword in keywords:

            if keyword in combined_text:

                matched_keywords += 1


        if matched_keywords > 0:

            matches.append(
                clean_task(task)
            )


    return matches


# ============================================================
# GET UPCOMING TASKS
# ============================================================

def get_upcoming_tasks_tool():

    tasks = get_upcoming_tasks()

    return [
        clean_task(task)
        for task in tasks
    ]


# ============================================================
# GET COMPLETED TASKS
# ============================================================

def get_completed_tasks_tool():

    tasks = get_completed_tasks()

    return [
        clean_task(task)
        for task in tasks
    ]


# ============================================================
# PRIORITIZE TASKS
# ============================================================

def prioritize_tasks_tool():

    tasks = get_pending_tasks()


    # Sort by:
    #
    # 1. Deadline
    # 2. High priority
    # 3. Medium priority
    # 4. Low priority

    tasks.sort(
        key=lambda task: (

            task.get(
                "deadline"
            ) or "9999-12-31",

            task.get(
                "priority"
            ) != "high",

            task.get(
                "priority"
            ) != "medium"
        )
    )


    return [
        clean_task(task)
        for task in tasks
    ]


# ============================================================
# GET ORIGINAL EMAIL
# ============================================================

def get_email_tool(message_id):

    service = connect_gmail()

    email = get_email_for_agent(
        service,
        message_id
    )

    return email


# ============================================================
# SEMANTIC SEARCH
# ============================================================

def semantic_search_tasks_tool(search_text):

    results = semantic_search_tasks(
        search_text
    )

    # semantic_search_tasks() already projects
    # only useful fields.
    #
    # We clean again for safety.

    return [
        clean_task(task)
        for task in results
    ]


# ============================================================
# HYBRID SEARCH
# ============================================================

def hybrid_search_tasks_tool(search_text):

    results = hybrid_search_tasks(
        search_text
    )

    # hybrid_search_tasks() already removes
    # the embedding.
    #
    # Clean again to guarantee that no embedding
    # can reach the LLM.

    cleaned_results = []

    for task in results:

        clean = clean_task(task)

        clean["keyword_score"] = task.get(
            "keyword_score",
            0
        )

        clean["semantic_score"] = task.get(
            "semantic_score",
            0
        )

        clean["hybrid_score"] = task.get(
            "hybrid_score",
            0
        )

        cleaned_results.append(
            clean
        )

    return cleaned_results


# ============================================================
# GET DRAFTS
# ============================================================

def get_drafts_tool(status=None):
    """Get email drafts, optionally filtered by status."""

    drafts = get_all_drafts(status)

    cleaned = []
    for draft in drafts:
        cleaned.append({
            "draft_id": draft.get("draft_id"),
            "message_id": draft.get("message_id"),
            "recipient": draft.get("recipient"),
            "subject": draft.get("subject"),
            "reply_type": draft.get("reply_type"),
            "status": draft.get("status"),
            "created_at": draft.get("created_at")
        })

    return cleaned


# ============================================================
# GET CALENDAR EVENTS
# ============================================================

def get_calendar_events_tool(max_results=10):
    """Get upcoming calendar events."""

    try:
        events = get_upcoming_calendar_events(
            max_results=max_results
        )
        return events
    except Exception as e:
        return {
            "error": str(e)
        }


# ============================================================
# TOOL DEFINITIONS
# ============================================================

tools = [

    # ========================================================
    # GET PENDING TASKS
    # ========================================================

    {
        "type": "function",

        "function": {

            "name": "get_pending_tasks",

            "description":
                "Get all pending actionable email tasks.",

            "parameters": {

                "type": "object",

                "properties": {},

                "required": []
            }
        }
    },


    # ========================================================
    # COMPLETE TASK
    # ========================================================

    {
        "type": "function",

        "function": {

            "name": "complete_task",

            "description":
                "Mark a pending task as completed using "
                "its email message ID.",

            "parameters": {

                "type": "object",

                "properties": {

                    "message_id": {

                        "type": "string",

                        "description":
                            "The Gmail message ID of the task."
                    }
                },

                "required": [
                    "message_id"
                ]
            }
        }
    },


    # ========================================================
    # FIND TASK
    # ========================================================

    {
        "type": "function",

        "function": {

            "name": "find_task",

            "description":
                "Find pending tasks using exact phrase "
                "or keyword matching. Use this when the "
                "user is looking for a specific task or "
                "specific words.",

            "parameters": {

                "type": "object",

                "properties": {

                    "search_text": {

                        "type": "string",

                        "description":
                            "Text or keywords to search for."
                    }
                },

                "required": [
                    "search_text"
                ]
            }
        }
    },


    # ========================================================
    # UPCOMING TASKS
    # ========================================================

    {
        "type": "function",

        "function": {

            "name": "get_upcoming_tasks",

            "description":
                "Get pending tasks that have upcoming "
                "deadlines.",

            "parameters": {

                "type": "object",

                "properties": {},

                "required": []
            }
        }
    },


    # ========================================================
    # COMPLETED TASKS
    # ========================================================

    {
        "type": "function",

        "function": {

            "name": "get_completed_tasks",

            "description":
                "Get tasks that have already been completed.",

            "parameters": {

                "type": "object",

                "properties": {},

                "required": []
            }
        }
    },


    # ========================================================
    # PRIORITIZE TASKS
    # ========================================================

    {
        "type": "function",

        "function": {

            "name": "prioritize_tasks",

            "description":
                "Return pending tasks ordered by deadline "
                "and priority.",

            "parameters": {

                "type": "object",

                "properties": {},

                "required": []
            }
        }
    },


    # ========================================================
    # GET EMAIL
    # ========================================================

    {
        "type": "function",

        "function": {

            "name": "get_email",

            "description":
                "Read the original Gmail email using its "
                "Gmail message ID. Use this when the user "
                "wants the complete original email content.",

            "parameters": {

                "type": "object",

                "properties": {

                    "message_id": {

                        "type": "string",

                        "description":
                            "The Gmail message ID."
                    }
                },

                "required": [
                    "message_id"
                ]
            }
        }
    },


    # ========================================================
    # SEMANTIC SEARCH
    # ========================================================

    {
        "type": "function",

        "function": {

            "name": "semantic_search_tasks",

            "description":
                "Search pending email tasks primarily "
                "by semantic meaning, topic, category, "
                "or concept. Use when exact keywords "
                "may not appear in the task.",

            "parameters": {

                "type": "object",

                "properties": {

                    "search_text": {

                        "type": "string",

                        "description":
                            "Natural-language search query."
                    }
                },

                "required": [
                    "search_text"
                ]
            }
        }
    },


    # ========================================================
    # HYBRID SEARCH
    # ========================================================

    {
        "type": "function",

        "function": {

            "name": "hybrid_search_tasks",

            "description":
                "Search pending email tasks using both "
                "keyword matching and semantic meaning. "
                "Use this for broad natural-language "
                "searches where both exact terms and "
                "conceptual meaning may be important.",

            "parameters": {

                "type": "object",

                "properties": {

                    "search_text": {

                        "type": "string",

                        "description":
                            "The user's natural-language "
                            "semantic search query."
                    }
                },

                "required": [
                    "search_text"
                ]
            }
        }
    },


    # ========================================================
    # GET DRAFTS
    # ========================================================

    {
        "type": "function",

        "function": {

            "name": "get_drafts",

            "description":
                "Get AI-generated email reply drafts. "
                "Optionally filter by status: draft, "
                "approved, sent, rejected.",

            "parameters": {

                "type": "object",

                "properties": {

                    "status": {

                        "type": "string",

                        "description":
                            "Optional status filter: "
                            "draft, approved, sent, "
                            "or rejected."
                    }
                },

                "required": []
            }
        }
    },


    # ========================================================
    # GET CALENDAR EVENTS
    # ========================================================

    {
        "type": "function",

        "function": {

            "name": "get_calendar_events",

            "description":
                "Get upcoming Google Calendar events.",

            "parameters": {

                "type": "object",

                "properties": {},

                "required": []
            }
        }
    }
]