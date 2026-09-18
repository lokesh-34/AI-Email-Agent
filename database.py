import os
import uuid
import logging

from datetime import datetime

from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

from embedding import create_embedding


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

logger = logging.getLogger(__name__)


# ============================================================
# MONGODB CONNECTION
# ============================================================

client = MongoClient(
    MONGODB_URI,
    server_api=ServerApi(
        version="1",
        strict=False,
        deprecation_errors=True
    )
)

db = client["academic_agent"]

tasks_collection = db["tasks"]

drafts_collection = db["email_drafts"]


# ============================================================
# ENSURE INDEXES
# ============================================================

def ensure_indexes():
    """Create indexes for performance and uniqueness."""

    try:
        tasks_collection.create_index(
            "message_id",
            unique=True,
            sparse=True
        )
        tasks_collection.create_index("status")
        tasks_collection.create_index("priority")
        tasks_collection.create_index("deadline")
        tasks_collection.create_index("category")

        drafts_collection.create_index(
            "draft_id",
            unique=True
        )
        drafts_collection.create_index("message_id")
        drafts_collection.create_index("status")

        logger.info("Database indexes ensured.")

    except Exception as e:
        logger.warning(
            "Index creation warning: %s", str(e)
        )


# ============================================================
# SAVE TASK
# ============================================================

def save_task(task):

    result = tasks_collection.insert_one(task)

    logger.info(
        "Task saved. ID: %s, Subject: %s",
        result.inserted_id,
        task.get("subject", "")
    )

    return result.inserted_id


# ============================================================
# CHECK WHETHER EMAIL ALREADY EXISTS
# ============================================================

def task_exists(message_id):

    task = tasks_collection.find_one({
        "message_id": message_id
    })

    return task is not None


# ============================================================
# GET PENDING TASKS
# ============================================================

def get_pending_tasks():

    tasks = tasks_collection.find({
        "status": "pending"
    })

    return list(tasks)


# ============================================================
# UPDATE TASK STATUS
# ============================================================

def update_task_status(message_id, status):

    result = tasks_collection.update_one(
        {
            "message_id": message_id
        },
        {
            "$set": {
                "status": status
            }
        }
    )

    return result.modified_count


# ============================================================
# GET UPCOMING TASKS
# ============================================================

def get_upcoming_tasks():

    today = datetime.now().strftime("%Y-%m-%d")

    tasks = tasks_collection.find({
        "status": "pending",
        "deadline": {
            "$gte": today
        }
    }).sort(
        "deadline",
        1
    )

    return list(tasks)


# ============================================================
# GET COMPLETED TASKS
# ============================================================

def get_completed_tasks():

    tasks = tasks_collection.find({
        "status": "completed"
    }).sort(
        "deadline",
        1
    )

    return list(tasks)


# ============================================================
# GET HIGH PRIORITY TASKS
# ============================================================

def get_high_priority_tasks():

    tasks = tasks_collection.find({
        "status": "pending",
        "priority": "high"
    })

    return list(tasks)


# ============================================================
# GET ALL TASKS
# ============================================================

def get_all_tasks(status=None):

    query = {}
    if status:
        query["status"] = status

    tasks = tasks_collection.find(query).sort(
        "deadline", 1
    )

    return list(tasks)


# ============================================================
# GET TASKS WITH EVENTS
# ============================================================

def get_tasks_with_events():

    tasks = tasks_collection.find({
        "event_required": True,
        "calendar_event_id": {"$ne": None}
    })

    return list(tasks)


# ============================================================
# SEMANTIC SEARCH
# ============================================================

def semantic_search_tasks(search_text, limit=5):

    # Create embedding for user's query
    query_vector = create_embedding(
        search_text
    )

    pipeline = [

        # ----------------------------------------------------
        # Vector search
        # ----------------------------------------------------

        {
            "$vectorSearch": {

                "index": "vector_index",

                "path": "embedding",

                "queryVector": query_vector,

                "numCandidates": 100,

                "limit": limit,

                "filter": {
                    "status": "pending"
                }
            }
        },

        # ----------------------------------------------------
        # Return only useful fields
        #
        # IMPORTANT:
        # Do NOT return the embedding.
        # The embedding is only needed by MongoDB
        # for vector similarity search.
        # ----------------------------------------------------

        {
            "$project": {

                "_id": 0,

                "message_id": 1,

                "sender": 1,

                "subject": 1,

                "title": 1,

                "action": 1,

                "category": 1,

                "action_required": 1,

                "deadline": 1,

                "priority": 1,

                "status": 1,

                "score": {
                    "$meta": "vectorSearchScore"
                }
            }
        }
    ]

    results = tasks_collection.aggregate(
        pipeline
    )

    return list(results)


# ============================================================
# UPDATE CALENDAR EVENT ID
# ============================================================

def update_calendar_event_id(
    message_id,
    calendar_event_id
):

    result = tasks_collection.update_one(

        {
            "message_id": message_id
        },

        {
            "$set": {
                "calendar_event_id":
                    calendar_event_id
            }
        }
    )

    return result.modified_count > 0


# ============================================================
# GET TASK BY MESSAGE ID
# ============================================================

def get_task_by_message_id(message_id):

    return tasks_collection.find_one(
        {
            "message_id": message_id
        }
    )


# ============================================================
# HYBRID SEARCH
# ============================================================

def hybrid_search_tasks(search_text, limit=5):

    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    MIN_HYBRID_SCORE = 0.50

    # --------------------------------------------------------
    # 1. Keyword search
    # --------------------------------------------------------

    keywords = search_text.lower().split()

    keyword_results = []

    pending_tasks = get_pending_tasks()

    for task in pending_tasks:

        searchable_text = " ".join([
            str(task.get("title", "")),
            str(task.get("action", "")),
            str(task.get("subject", "")),
            str(task.get("sender", "")),
            str(task.get("category", ""))
        ]).lower()

        matched_keywords = sum(
            1
            for keyword in keywords
            if keyword in searchable_text
        )

        if matched_keywords > 0:

            keyword_results.append({
                "task": task,
                "keyword_score": matched_keywords
            })

    # --------------------------------------------------------
    # 2. Semantic search
    # --------------------------------------------------------

    semantic_results = semantic_search_tasks(
        search_text,
        limit=limit
    )

    # --------------------------------------------------------
    # 3. Combine keyword + semantic results
    # --------------------------------------------------------

    combined = {}

    # --------------------------------------------------------
    # Add keyword results
    # --------------------------------------------------------

    for item in keyword_results:

        task = item["task"]

        message_id = task["message_id"]

        combined[message_id] = {
            "task": task,
            "keyword_score": item["keyword_score"],
            "semantic_score": 0
        }

    # --------------------------------------------------------
    # Add semantic results
    # --------------------------------------------------------

    for task in semantic_results:

        message_id = task["message_id"]

        semantic_score = task.get(
            "score",
            0
        )

        if message_id in combined:

            combined[message_id]["semantic_score"] = (
                semantic_score
            )

        else:

            combined[message_id] = {
                "task": task,
                "keyword_score": 0,
                "semantic_score": semantic_score
            }

    # --------------------------------------------------------
    # 4. Calculate hybrid score
    # --------------------------------------------------------

    results = []

    for item in combined.values():

        task = item["task"]

        keyword_score = item.get(
            "keyword_score",
            0
        )

        semantic_score = item.get(
            "semantic_score",
            0
        )

        # ----------------------------------------------------
        # Normalize keyword score
        # ----------------------------------------------------

        keyword_component = min(
            keyword_score / max(len(keywords), 1),
            1
        )

        # ----------------------------------------------------
        # Combine scores
        #
        # 40% keyword
        # 60% semantic
        # ----------------------------------------------------

        hybrid_score = (
            0.4 * keyword_component
            +
            0.6 * semantic_score
        )

        # ----------------------------------------------------
        # Remove weak/unrelated results
        # ----------------------------------------------------

        if hybrid_score < MIN_HYBRID_SCORE:
            continue

        # ----------------------------------------------------
        # IMPORTANT
        #
        # Return ONLY fields required by the agent.
        #
        # DO NOT return:
        #
        #     embedding
        #
        # Otherwise the 384-dimensional vectors will be
        # sent to Groq and consume thousands of tokens.
        # ----------------------------------------------------

        clean_task = {

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

            # Search scores
            "keyword_score": keyword_score,

            "semantic_score": semantic_score,

            "hybrid_score": hybrid_score
        }

        results.append(
            clean_task
        )

    # --------------------------------------------------------
    # 5. Sort by hybrid score
    # --------------------------------------------------------

    results.sort(
        key=lambda task: task.get(
            "hybrid_score",
            0
        ),
        reverse=True
    )

    # --------------------------------------------------------
    # 6. Return top results
    # --------------------------------------------------------

    return results[:limit]


# ============================================================
# EMAIL DRAFTS
# ============================================================

def save_draft(draft):
    """Save a new email draft to MongoDB."""

    result = drafts_collection.insert_one(draft)

    logger.info(
        "Draft saved. ID: %s, To: %s",
        draft.get("draft_id"),
        draft.get("recipient")
    )

    return result.inserted_id


def draft_exists_for_message(message_id):
    """Check if a draft already exists for a message."""

    draft = drafts_collection.find_one({
        "message_id": message_id
    })

    return draft is not None


def get_draft_by_id(draft_id):
    """Get a single draft by draft_id."""

    return drafts_collection.find_one({
        "draft_id": draft_id
    })


def get_all_drafts(status=None):
    """Get all drafts, optionally filtered by status."""

    query = {}
    if status:
        query["status"] = status

    drafts = drafts_collection.find(query).sort(
        "created_at", -1
    )

    return list(drafts)


def update_draft(draft_id, updates):
    """Update draft fields (recipient, subject, body)."""

    updates["updated_at"] = (
        datetime.utcnow().isoformat()
    )

    result = drafts_collection.update_one(
        {"draft_id": draft_id},
        {"$set": updates}
    )

    logger.info(
        "Draft updated. ID: %s", draft_id
    )

    return result.modified_count > 0


def approve_draft(draft_id):
    """Mark a draft as approved."""

    result = drafts_collection.update_one(
        {
            "draft_id": draft_id,
            "status": "draft"
        },
        {
            "$set": {
                "status": "approved",
                "approved_at": (
                    datetime.utcnow().isoformat()
                ),
                "updated_at": (
                    datetime.utcnow().isoformat()
                )
            }
        }
    )

    return result.modified_count > 0


def reject_draft(draft_id):
    """Mark a draft as rejected."""

    result = drafts_collection.update_one(
        {
            "draft_id": draft_id,
            "status": {"$in": ["draft", "approved"]}
        },
        {
            "$set": {
                "status": "rejected",
                "updated_at": (
                    datetime.utcnow().isoformat()
                )
            }
        }
    )

    return result.modified_count > 0


def mark_draft_sent(draft_id, gmail_message_id):
    """Mark a draft as sent with Gmail message ID."""

    result = drafts_collection.update_one(
        {
            "draft_id": draft_id,
            "status": {"$in": ["draft", "approved"]}
        },
        {
            "$set": {
                "status": "sent",
                "gmail_message_id": gmail_message_id,
                "sent_at": (
                    datetime.utcnow().isoformat()
                ),
                "updated_at": (
                    datetime.utcnow().isoformat()
                )
            }
        }
    )

    return result.modified_count > 0


def create_draft_from_ai(message_id, ai_result):
    """Create a draft document from AI parsing result."""

    draft = {
        "draft_id": str(uuid.uuid4()),
        "message_id": message_id,
        "recipient": ai_result.get("reply_recipient"),
        "subject": ai_result.get("reply_subject"),
        "body": ai_result.get("reply_draft"),
        "original_body": ai_result.get("reply_draft"),
        "reply_type": ai_result.get("reply_type"),
        "status": "draft",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "approved_at": None,
        "sent_at": None,
        "gmail_message_id": None
    }

    return draft


# ============================================================
# DASHBOARD STATS
# ============================================================

def get_dashboard_stats():
    """Get statistics for the dashboard."""

    pending_count = tasks_collection.count_documents(
        {"status": "pending"}
    )

    high_priority_count = tasks_collection.count_documents(
        {"status": "pending", "priority": "high"}
    )

    today = datetime.now().strftime("%Y-%m-%d")

    upcoming_events_count = tasks_collection.count_documents(
        {
            "event_required": True,
            "event_date": {"$gte": today}
        }
    )

    draft_count = drafts_collection.count_documents(
        {"status": {"$in": ["draft", "approved"]}}
    )

    return {
        "pending_tasks": pending_count,
        "high_priority": high_priority_count,
        "upcoming_events": upcoming_events_count,
        "draft_replies": draft_count
    }