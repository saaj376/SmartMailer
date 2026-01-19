"""
Email scheduling utilities for SmartMailer.
Provides functionality to schedule emails to be sent at a specific time.
"""
from datetime import datetime, timedelta
import time
from typing import Optional


class EmailScheduler:
    """Handles scheduling of emails to be sent at a future time."""
    
    @staticmethod
    def calculate_delay(scheduled_time: datetime) -> float:
        """
        Calculate the delay in seconds until the scheduled time.
        
        Args:
            scheduled_time: The datetime when the email should be sent
            
        Returns:
            Delay in seconds. Returns 0 if scheduled time is in the past.
        """
        now = datetime.now()
        if scheduled_time <= now:
            return 0.0
        
        delta = scheduled_time - now
        return delta.total_seconds()
    
    @staticmethod
    def wait_until(scheduled_time: datetime, check_interval: float = 1.0) -> None:
        """
        Wait until the scheduled time arrives.
        
        Args:
            scheduled_time: The datetime when to stop waiting
            check_interval: How often to check the time (in seconds)
        """
        while datetime.now() < scheduled_time:
            delay = EmailScheduler.calculate_delay(scheduled_time)
            if delay <= 0:
                break
            # Sleep for the minimum of check_interval or remaining delay
            sleep_time = min(check_interval, delay)
            time.sleep(sleep_time)
    
    @staticmethod
    def parse_schedule_time(schedule_str: Optional[str]) -> Optional[datetime]:
        """
        Parse a schedule time string into a datetime object.
        
        Supported formats:
        - ISO format: "2024-12-25 14:30:00"
        - Relative: "+1h", "+30m", "+2d" (hours, minutes, days)
        
        Args:
            schedule_str: String representation of the schedule time
            
        Returns:
            datetime object or None if no schedule string provided
        """
        if not schedule_str:
            return None
        
        # Handle relative time format
        if schedule_str.startswith('+'):
            value_str = schedule_str[1:-1]
            unit = schedule_str[-1].lower()
            
            try:
                value = int(value_str)
            except ValueError:
                raise ValueError(f"Invalid relative time format: {schedule_str}")
            
            now = datetime.now()
            if unit == 'h':
                return now + timedelta(hours=value)
            elif unit == 'm':
                return now + timedelta(minutes=value)
            elif unit == 'd':
                return now + timedelta(days=value)
            elif unit == 's':
                return now + timedelta(seconds=value)
            else:
                raise ValueError(f"Unknown time unit: {unit}. Use 's', 'm', 'h', or 'd'")
        
        # Handle ISO format
        try:
            return datetime.fromisoformat(schedule_str)
        except ValueError:
            raise ValueError(f"Invalid datetime format: {schedule_str}. Use ISO format or relative time (+1h, +30m, +2d)")
