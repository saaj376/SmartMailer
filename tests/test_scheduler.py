import pytest
from datetime import datetime, timedelta
from smartmailer.utils.scheduler import EmailScheduler


def test_calculate_delay_future_time():
    """Test delay calculation for future time"""
    future_time = datetime.now() + timedelta(seconds=10)
    delay = EmailScheduler.calculate_delay(future_time)
    assert 9 <= delay <= 11  # Allow 1 second tolerance


def test_calculate_delay_past_time():
    """Test delay calculation for past time returns 0"""
    past_time = datetime.now() - timedelta(seconds=10)
    delay = EmailScheduler.calculate_delay(past_time)
    assert delay == 0.0


def test_parse_schedule_time_iso_format():
    """Test parsing ISO format datetime string"""
    schedule_str = "2025-12-25 14:30:00"
    result = EmailScheduler.parse_schedule_time(schedule_str)
    assert result == datetime(2025, 12, 25, 14, 30, 0)


def test_parse_schedule_time_relative_hours():
    """Test parsing relative time in hours"""
    before = datetime.now()
    result = EmailScheduler.parse_schedule_time("+2h")
    after = datetime.now()
    
    # Check that result is approximately 2 hours in the future
    expected_min = before + timedelta(hours=2)
    expected_max = after + timedelta(hours=2)
    assert expected_min <= result <= expected_max


def test_parse_schedule_time_relative_minutes():
    """Test parsing relative time in minutes"""
    before = datetime.now()
    result = EmailScheduler.parse_schedule_time("+30m")
    after = datetime.now()
    
    expected_min = before + timedelta(minutes=30)
    expected_max = after + timedelta(minutes=30)
    assert expected_min <= result <= expected_max


def test_parse_schedule_time_relative_days():
    """Test parsing relative time in days"""
    before = datetime.now()
    result = EmailScheduler.parse_schedule_time("+1d")
    after = datetime.now()
    
    expected_min = before + timedelta(days=1)
    expected_max = after + timedelta(days=1)
    assert expected_min <= result <= expected_max


def test_parse_schedule_time_relative_seconds():
    """Test parsing relative time in seconds"""
    before = datetime.now()
    result = EmailScheduler.parse_schedule_time("+60s")
    after = datetime.now()
    
    expected_min = before + timedelta(seconds=60)
    expected_max = after + timedelta(seconds=60)
    assert expected_min <= result <= expected_max


def test_parse_schedule_time_none():
    """Test that None input returns None"""
    result = EmailScheduler.parse_schedule_time(None)
    assert result is None


def test_parse_schedule_time_empty_string():
    """Test that empty string returns None"""
    result = EmailScheduler.parse_schedule_time("")
    assert result is None


def test_parse_schedule_time_invalid_format():
    """Test that invalid format raises ValueError"""
    with pytest.raises(ValueError, match="Invalid datetime format"):
        EmailScheduler.parse_schedule_time("not-a-date")


def test_parse_schedule_time_invalid_relative_unit():
    """Test that invalid relative time unit raises ValueError"""
    with pytest.raises(ValueError, match="Unknown time unit"):
        EmailScheduler.parse_schedule_time("+5x")


def test_parse_schedule_time_invalid_relative_value():
    """Test that invalid relative time value raises ValueError"""
    with pytest.raises(ValueError, match="Invalid relative time format"):
        EmailScheduler.parse_schedule_time("+abch")


def test_wait_until_immediate():
    """Test waiting until a time in the past returns immediately"""
    past_time = datetime.now() - timedelta(seconds=1)
    start = datetime.now()
    EmailScheduler.wait_until(past_time, check_interval=0.1)
    end = datetime.now()
    elapsed = (end - start).total_seconds()
    assert elapsed < 0.5  # Should return almost immediately


def test_wait_until_short_delay():
    """Test waiting for a short period"""
    future_time = datetime.now() + timedelta(seconds=1)
    start = datetime.now()
    EmailScheduler.wait_until(future_time, check_interval=0.1)
    end = datetime.now()
    elapsed = (end - start).total_seconds()
    assert 0.9 <= elapsed <= 1.5  # Allow some tolerance
