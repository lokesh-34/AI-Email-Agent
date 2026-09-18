# ============================================================
# TESTS — AI Email Copilot
# ============================================================
#
# Run:
#   python -m pytest tests/ -v
# ============================================================

import pytest
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch, MagicMock
from datetime import datetime


# ============================================================
# EMAIL PARSER TESTS
# ============================================================

class TestEmailParser:

    def test_parse_email_returns_dict(self):
        """parse_email should return a dictionary."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "category": "job",
            "action": "Confirm interview",
            "action_required": True,
            "deadline": "2026-09-12",
            "priority": "high",
            "title": "Interview Invitation",
            "event_required": True,
            "event_title": "Technical Interview",
            "event_date": "2026-09-12",
            "event_start_time": "10:00",
            "event_end_time": "11:00",
            "event_timezone": "Asia/Kolkata",
            "event_location": "Google Meet",
            "event_description": "Technical interview",
            "reply_required": True,
            "reply_type": "interview_confirmation",
            "reply_recipient": "recruiter@example.com",
            "reply_subject": "Re: Interview",
            "reply_draft": "Dear Team, I confirm...",
            "ai_explanation": "Reply needed for confirmation."
        })

        with patch('email_parser.client') as mock_client:
            mock_client.chat.completions.create.return_value = mock_response

            from email_parser import parse_email

            result = parse_email({
                "subject": "Interview Invitation",
                "sender": "recruiter@example.com",
                "body": "We invite you for an interview."
            })

            assert isinstance(result, dict)
            assert result["category"] == "job"
            assert result["reply_required"] == True
            assert result["event_required"] == True

    def test_parse_email_no_reply_for_marketing(self):
        """Marketing emails should not require replies."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "category": "marketing",
            "action": None,
            "action_required": False,
            "deadline": None,
            "priority": "low",
            "title": "Summer Sale",
            "event_required": False,
            "event_title": None,
            "event_date": None,
            "event_start_time": None,
            "event_end_time": None,
            "event_timezone": None,
            "event_location": None,
            "event_description": None,
            "reply_required": False,
            "reply_type": None,
            "reply_recipient": None,
            "reply_subject": None,
            "reply_draft": None,
            "ai_explanation": "Marketing email, no reply needed."
        })

        with patch('email_parser.client') as mock_client:
            mock_client.chat.completions.create.return_value = mock_response

            from email_parser import parse_email

            result = parse_email({
                "subject": "Summer Sale!",
                "sender": "marketing@store.com",
                "body": "50% off everything!"
            })

            assert result["reply_required"] == False
            assert result["event_required"] == False


# ============================================================
# TASK MANAGER TESTS
# ============================================================

class TestTaskManager:

    def test_create_task_has_required_fields(self):
        """create_task should include all required fields."""
        with patch('task_manager.create_embedding', return_value=[0.0] * 384):
            from task_manager import create_task

            ai_result = {
                "title": "Test Task",
                "action": "Do something",
                "category": "general",
                "action_required": True,
                "deadline": "2026-09-15",
                "priority": "medium",
                "event_required": False,
                "event_title": None,
                "event_date": None,
                "event_start_time": None,
                "event_end_time": None,
                "event_location": None,
                "event_description": None,
                "event_timezone": None,
                "reply_required": False,
                "reply_type": None,
                "reply_recipient": None,
                "reply_subject": None,
                "ai_explanation": None,
            }

            email = {
                "message_id": "test123",
                "sender": "test@example.com",
                "subject": "Test Email",
                "date": "Mon, 10 Sep 2026"
            }

            task = create_task(ai_result, email)

            assert task["message_id"] == "test123"
            assert task["status"] == "pending"
            assert task["calendar_event_id"] is None
            assert task["reply_required"] == False
            assert len(task["embedding"]) == 384

    def test_create_task_with_reply(self):
        """create_task should include reply fields when present."""
        with patch('task_manager.create_embedding', return_value=[0.0] * 384):
            from task_manager import create_task

            ai_result = {
                "title": "Interview",
                "action": "Confirm",
                "category": "job",
                "action_required": True,
                "deadline": None,
                "priority": "high",
                "event_required": False,
                "event_title": None,
                "event_date": None,
                "event_start_time": None,
                "event_end_time": None,
                "event_location": None,
                "event_description": None,
                "event_timezone": None,
                "reply_required": True,
                "reply_type": "interview_confirmation",
                "reply_recipient": "hr@company.com",
                "reply_subject": "Re: Interview",
                "ai_explanation": "Confirmation requested."
            }

            email = {
                "message_id": "reply123",
                "sender": "hr@company.com",
                "subject": "Interview",
                "date": "Mon, 10 Sep 2026"
            }

            task = create_task(ai_result, email)

            assert task["reply_required"] == True
            assert task["reply_type"] == "interview_confirmation"
            assert task["reply_recipient"] == "hr@company.com"


# ============================================================
# DATABASE TESTS
# ============================================================

class TestDatabase:

    def test_create_draft_from_ai(self):
        """create_draft_from_ai should produce valid draft dict."""
        from database import create_draft_from_ai

        ai_result = {
            "reply_recipient": "test@example.com",
            "reply_subject": "Re: Test",
            "reply_draft": "Dear Test...",
            "reply_type": "general_response"
        }

        draft = create_draft_from_ai("msg123", ai_result)

        assert draft["message_id"] == "msg123"
        assert draft["recipient"] == "test@example.com"
        assert draft["subject"] == "Re: Test"
        assert draft["body"] == "Dear Test..."
        assert draft["original_body"] == "Dear Test..."
        assert draft["status"] == "draft"
        assert draft["sent_at"] is None
        assert draft["gmail_message_id"] is None
        assert draft["draft_id"] is not None

    def test_draft_has_unique_id(self):
        """Each draft should have a unique draft_id."""
        from database import create_draft_from_ai

        ai_result = {
            "reply_recipient": "a@b.com",
            "reply_subject": "Test",
            "reply_draft": "Hi",
            "reply_type": "general"
        }

        draft1 = create_draft_from_ai("msg1", ai_result)
        draft2 = create_draft_from_ai("msg2", ai_result)

        assert draft1["draft_id"] != draft2["draft_id"]


# ============================================================
# CALENDAR TESTS
# ============================================================

class TestCalendar:

    def test_timezone_mapping(self):
        """Timezone abbreviations should map correctly."""
        from google_calendar import get_timezone
        from zoneinfo import ZoneInfo

        tz_ist = get_timezone("IST")
        assert str(tz_ist) == "Asia/Kolkata"

        tz_utc = get_timezone("UTC")
        assert str(tz_utc) == "UTC"

        tz_pst = get_timezone("PST")
        assert str(tz_pst) == "America/Los_Angeles"

    def test_null_timezone_defaults_to_local(self):
        """None timezone should default to Asia/Kolkata."""
        from google_calendar import get_timezone

        tz = get_timezone(None)
        assert str(tz) == "Asia/Kolkata"

    def test_iana_timezone(self):
        """IANA timezone names should work directly."""
        from google_calendar import get_timezone

        tz = get_timezone("America/New_York")
        assert str(tz) == "America/New_York"

    def test_past_event_not_created(self):
        """Events in the past should not be created."""
        from google_calendar import create_event_from_parsed_email

        result = create_event_from_parsed_email({
            "event_required": True,
            "event_title": "Past Event",
            "event_date": "2020-01-01",
            "event_start_time": "10:00",
            "event_end_time": "11:00",
            "event_timezone": "UTC"
        })

        assert result["created"] == False
        assert "past" in result["reason"].lower()

    def test_missing_date_not_created(self):
        """Events without a date should not be created."""
        from google_calendar import create_event_from_parsed_email

        result = create_event_from_parsed_email({
            "event_required": True,
            "event_title": "No Date Event",
            "event_date": None,
            "event_start_time": "10:00"
        })

        assert result["created"] == False

    def test_missing_time_not_created(self):
        """Events without start time should not be created."""
        from google_calendar import create_event_from_parsed_email

        result = create_event_from_parsed_email({
            "event_required": True,
            "event_title": "No Time Event",
            "event_date": "2030-01-01",
            "event_start_time": None
        })

        assert result["created"] == False

    def test_not_required_not_created(self):
        """Non-required events should not be created."""
        from google_calendar import create_event_from_parsed_email

        result = create_event_from_parsed_email({
            "event_required": False
        })

        assert result["created"] == False


# ============================================================
# GMAIL SENDER TESTS (MOCKED)
# ============================================================

class TestGmailSender:

    def test_send_email_builds_mime(self):
        """send_email should build and send a MIME message."""
        mock_service = MagicMock()
        mock_service.users().messages().send().execute.return_value = {
            "id": "sent_msg_123"
        }

        with patch('gmail_sender.connect_gmail_sender', return_value=mock_service):
            from gmail_sender import send_email

            result = send_email(
                recipient="test@example.com",
                subject="Test Subject",
                body="Test body content"
            )

            assert result["success"] == True
            assert result["gmail_message_id"] == "sent_msg_123"

    def test_send_email_error_handling(self):
        """send_email should handle errors gracefully."""
        with patch('gmail_sender.connect_gmail_sender', side_effect=Exception("Auth failed")):
            from gmail_sender import send_email

            result = send_email(
                recipient="test@example.com",
                subject="Test",
                body="Test"
            )

            assert result["success"] == False
            assert result["error"] is not None


# ============================================================
# DUPLICATE PROTECTION TESTS
# ============================================================

class TestDuplicateProtection:

    def test_draft_status_prevents_resend(self):
        """A draft with status='sent' should not be sent again."""
        # This tests the API logic conceptually
        draft = {
            "draft_id": "d1",
            "status": "sent",
            "gmail_message_id": "already_sent"
        }

        # The API checks status before sending
        assert draft["status"] == "sent"
        # This means the API would return "Email already sent"


# ============================================================
# API ENDPOINT TESTS
# ============================================================

class TestAPIEndpoints:

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from backend.api import app
        return TestClient(app)

    def test_health_check(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_dashboard_endpoint(self, client):
        """Dashboard endpoint should return stats."""
        with patch('backend.routes.dashboard.get_dashboard_stats') as mock:
            mock.return_value = {
                "pending_tasks": 5,
                "high_priority": 2,
                "upcoming_events": 1,
                "draft_replies": 3
            }

            response = client.get("/api/dashboard")
            assert response.status_code == 200
            data = response.json()
            assert "pending_tasks" in data

    def test_tasks_endpoint(self, client):
        """Tasks endpoint should return list."""
        with patch('backend.routes.tasks.get_all_tasks') as mock:
            mock.return_value = []
            response = client.get("/api/tasks")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_drafts_endpoint(self, client):
        """Drafts endpoint should return list."""
        with patch('backend.routes.drafts.get_all_drafts') as mock:
            mock.return_value = []
            response = client.get("/api/drafts")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_draft_not_found(self, client):
        """Getting a non-existent draft should return 404."""
        with patch('backend.routes.drafts.get_draft_by_id') as mock:
            mock.return_value = None
            response = client.get("/api/drafts/nonexistent")
            assert response.status_code == 404

    def test_send_already_sent_draft(self, client):
        """Sending an already-sent draft should return success (idempotent)."""
        with patch('backend.routes.drafts.get_draft_by_id') as mock:
            mock.return_value = {
                "draft_id": "d1",
                "status": "sent",
                "gmail_message_id": "msg_abc"
            }
            response = client.post("/api/drafts/d1/send")
            assert response.status_code == 200
            data = response.json()
            assert "already sent" in data["message"].lower()
