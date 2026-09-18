# ============================================================
# PYDANTIC MODELS
# ============================================================

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================
# DRAFT MODELS
# ============================================================

class DraftUpdate(BaseModel):
    """Request body for updating a draft."""
    recipient: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None


class DraftResponse(BaseModel):
    """Response model for a draft."""
    draft_id: str
    message_id: str
    recipient: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    original_body: Optional[str] = None
    reply_type: Optional[str] = None
    status: str = "draft"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    approved_at: Optional[str] = None
    sent_at: Optional[str] = None
    gmail_message_id: Optional[str] = None


# ============================================================
# TASK MODELS
# ============================================================

class TaskResponse(BaseModel):
    """Response model for a task."""
    message_id: str
    sender: Optional[str] = None
    subject: Optional[str] = None
    date: Optional[str] = None
    title: Optional[str] = None
    action: Optional[str] = None
    category: Optional[str] = None
    action_required: Optional[bool] = None
    deadline: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    event_required: Optional[bool] = None
    event_title: Optional[str] = None
    event_date: Optional[str] = None
    event_start_time: Optional[str] = None
    event_end_time: Optional[str] = None
    event_timezone: Optional[str] = None
    event_location: Optional[str] = None
    event_description: Optional[str] = None
    calendar_event_id: Optional[str] = None
    reply_required: Optional[bool] = None
    reply_type: Optional[str] = None
    reply_recipient: Optional[str] = None
    reply_subject: Optional[str] = None
    ai_explanation: Optional[str] = None


# ============================================================
# DASHBOARD MODELS
# ============================================================

class DashboardStats(BaseModel):
    """Dashboard statistics."""
    pending_tasks: int = 0
    high_priority: int = 0
    upcoming_events: int = 0
    draft_replies: int = 0


# ============================================================
# NOTIFICATION MODEL
# ============================================================

class NotificationItem(BaseModel):
    """A notification item."""
    id: str
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    category: Optional[str] = None
    type: str = "task"
    date: Optional[str] = None
    action: Optional[str] = None
    message_id: Optional[str] = None
    draft_id: Optional[str] = None


# ============================================================
# AGENT MODELS
# ============================================================

class AgentChatRequest(BaseModel):
    """Request body for agent chat."""
    message: str
    conversation_history: Optional[List[dict]] = None


class AgentChatResponse(BaseModel):
    """Response from agent chat."""
    response: str
    conversation_history: List[dict]


# ============================================================
# PROCESSING MODELS
# ============================================================

class ProcessingResult(BaseModel):
    """Result of email processing."""
    processed: int = 0
    tasks_created: int = 0
    events_created: int = 0
    drafts_created: int = 0
    errors: int = 0


# ============================================================
# EMAIL MODELS
# ============================================================

class EmailResponse(BaseModel):
    """Response model for an email."""
    message_id: str
    sender: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    date: Optional[str] = None


# ============================================================
# CALENDAR EVENT MODEL
# ============================================================

class CalendarEventResponse(BaseModel):
    """Response model for a calendar event."""
    event_id: Optional[str] = None
    title: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    html_link: Optional[str] = None


# ============================================================
# GENERIC RESPONSE
# ============================================================

class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True
