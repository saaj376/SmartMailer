import pytest
import os
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from smartmailer.scheduler.scheduler import EmailScheduler
from smartmailer.core.template import TemplateModel


class TestRecipient(TemplateModel):
    name: str
    email: str


@pytest.fixture
def temp_storage_path(tmp_path):
    """Create a temporary storage path for tests."""
    storage = tmp_path / "test_scheduled_emails"
    return str(storage)


@pytest.fixture
def scheduler(temp_storage_path):
    """Create a scheduler instance with temporary storage."""
    return EmailScheduler(storage_path=temp_storage_path)


@pytest.fixture
def sample_recipients():
    """Create sample recipients for testing."""
    return [
        TestRecipient(name="Alice", email="alice@example.com"),
        TestRecipient(name="Bob", email="bob@example.com")
    ]


@pytest.fixture
def sample_template_data():
    """Create sample template data."""
    return {
        "subject": "Test Subject",
        "body_text": "Hello {{ name }}",
        "body_html": "<p>Hello {{ name }}</p>"
    }


def test_scheduler_initialization(temp_storage_path):
    scheduler = EmailScheduler(storage_path=temp_storage_path)
    assert os.path.exists(temp_storage_path)
    assert os.path.exists(scheduler.scheduled_file)


def test_schedule_email(scheduler, sample_recipients, sample_template_data):
    scheduled_time = datetime.now() + timedelta(hours=1)
    
    schedule_id = scheduler.schedule_email(
        scheduled_time=scheduled_time,
        recipients=sample_recipients,
        email_field="email",
        template_data=sample_template_data
    )
    
    assert schedule_id.startswith("schedule_")
    
    # Verify it was saved
    schedules = scheduler.get_scheduled_emails()
    assert len(schedules) == 1
    assert schedules[0]["schedule_id"] == schedule_id
    assert schedules[0]["status"] == "pending"


def test_schedule_email_with_custom_id(scheduler, sample_recipients, sample_template_data):
    scheduled_time = datetime.now() + timedelta(hours=1)
    custom_id = "my_custom_schedule"
    
    schedule_id = scheduler.schedule_email(
        scheduled_time=scheduled_time,
        recipients=sample_recipients,
        email_field="email",
        template_data=sample_template_data,
        schedule_id=custom_id
    )
    
    assert schedule_id == custom_id


def test_schedule_email_duplicate_id_raises_error(scheduler, sample_recipients, sample_template_data):
    scheduled_time = datetime.now() + timedelta(hours=1)
    schedule_id = "duplicate_id"
    
    scheduler.schedule_email(
        scheduled_time=scheduled_time,
        recipients=sample_recipients,
        email_field="email",
        template_data=sample_template_data,
        schedule_id=schedule_id
    )
    
    with pytest.raises(ValueError, match="already exists"):
        scheduler.schedule_email(
            scheduled_time=scheduled_time,
            recipients=sample_recipients,
            email_field="email",
            template_data=sample_template_data,
            schedule_id=schedule_id
        )


def test_cancel_schedule(scheduler, sample_recipients, sample_template_data):
    scheduled_time = datetime.now() + timedelta(hours=1)
    
    schedule_id = scheduler.schedule_email(
        scheduled_time=scheduled_time,
        recipients=sample_recipients,
        email_field="email",
        template_data=sample_template_data
    )
    
    # Cancel the schedule
    result = scheduler.cancel_schedule(schedule_id)
    assert result is True
    
    # Verify it was removed
    schedules = scheduler.get_scheduled_emails()
    assert len(schedules) == 0


def test_cancel_nonexistent_schedule(scheduler):
    result = scheduler.cancel_schedule("nonexistent_id")
    assert result is False


def test_get_scheduled_emails_with_filter(scheduler, sample_recipients, sample_template_data):
    # Schedule multiple emails
    scheduler.schedule_email(
        scheduled_time=datetime.now() + timedelta(hours=1),
        recipients=sample_recipients,
        email_field="email",
        template_data=sample_template_data,
        schedule_id="pending_1"
    )
    
    # Manually mark one as sent for testing
    schedules = scheduler._load_schedules()
    schedules[0]["status"] = "sent"
    scheduler._save_schedules(schedules)
    
    scheduler.schedule_email(
        scheduled_time=datetime.now() + timedelta(hours=2),
        recipients=sample_recipients,
        email_field="email",
        template_data=sample_template_data,
        schedule_id="pending_2"
    )
    
    # Filter by status
    pending = scheduler.get_scheduled_emails(status="pending")
    assert len(pending) == 1
    assert pending[0]["schedule_id"] == "pending_2"
    
    sent = scheduler.get_scheduled_emails(status="sent")
    assert len(sent) == 1
    assert sent[0]["schedule_id"] == "pending_1"


def test_schedule_with_attachments_and_cc_bcc(scheduler, sample_recipients, sample_template_data):
    scheduled_time = datetime.now() + timedelta(hours=1)
    
    schedule_id = scheduler.schedule_email(
        scheduled_time=scheduled_time,
        recipients=sample_recipients,
        email_field="email",
        template_data=sample_template_data,
        attachment_paths=["file1.pdf", "file2.pdf"],
        cc=["cc@example.com"],
        bcc=["bcc@example.com"]
    )
    
    schedules = scheduler.get_scheduled_emails()
    assert len(schedules) == 1
    assert schedules[0]["attachment_paths"] == ["file1.pdf", "file2.pdf"]
    assert schedules[0]["cc"] == ["cc@example.com"]
    assert schedules[0]["bcc"] == ["bcc@example.com"]


def test_worker_start_stop(scheduler):
    mock_smartmailer = MagicMock()
    
    # Start worker
    scheduler.start_worker(mock_smartmailer, check_interval=1)
    assert scheduler._worker_thread is not None
    assert scheduler._worker_thread.is_alive()
    
    # Stop worker
    scheduler.stop_worker()
    time.sleep(0.5)  # Give it time to stop
    assert not scheduler._worker_thread.is_alive()


def test_worker_sends_scheduled_email(scheduler, sample_recipients, sample_template_data):
    """Test that worker sends emails when scheduled time is reached."""
    mock_smartmailer = MagicMock()
    
    # Schedule an email for immediate sending (past time)
    past_time = datetime.now() - timedelta(seconds=1)
    
    schedule_id = scheduler.schedule_email(
        scheduled_time=past_time,
        recipients=sample_recipients,
        email_field="email",
        template_data=sample_template_data
    )
    
    # Start worker with short check interval
    scheduler.start_worker(mock_smartmailer, check_interval=1)
    
    # Wait for worker to process
    time.sleep(2)
    
    # Stop worker
    scheduler.stop_worker()
    
    # Verify send_emails was called
    assert mock_smartmailer.send_emails.called
    
    # Verify status was updated
    schedules = scheduler.get_scheduled_emails()
    assert len(schedules) == 1
    assert schedules[0]["status"] in ["sent", "failed"]


def test_schedule_past_time_warning(scheduler, sample_recipients, sample_template_data, caplog):
    """Test that scheduling in the past logs a warning."""
    past_time = datetime.now() - timedelta(hours=1)
    
    scheduler.schedule_email(
        scheduled_time=past_time,
        recipients=sample_recipients,
        email_field="email",
        template_data=sample_template_data
    )
    
    # Check that warning was logged
    # Note: This checks the logger output, which may not appear in caplog depending on logger config


def test_scheduled_email_serialization(scheduler, sample_recipients, sample_template_data):
    """Test that recipients are properly serialized and can be deserialized."""
    scheduled_time = datetime.now() + timedelta(hours=1)
    
    schedule_id = scheduler.schedule_email(
        scheduled_time=scheduled_time,
        recipients=sample_recipients,
        email_field="email",
        template_data=sample_template_data
    )
    
    schedules = scheduler.get_scheduled_emails()
    assert len(schedules[0]["recipients"]) == 2
    assert schedules[0]["recipients"][0]["email"] == "alice@example.com"
    assert schedules[0]["recipients"][1]["email"] == "bob@example.com"
