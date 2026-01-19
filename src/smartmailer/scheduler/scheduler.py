import json
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from smartmailer.utils.new_logger import Logger
from smartmailer.utils.types import TemplateModelType


class EmailScheduler:
    """
    EmailScheduler manages scheduled email sending.
    It stores scheduled emails and checks periodically to send them at the right time.
    """
    
    def __init__(self, storage_path: str = "scheduled_emails", log_to_file: bool = False, log_level: str = 'INFO'):
        """
        Initialize the EmailScheduler.
        
        Args:
            storage_path: Directory path where scheduled emails will be stored
            log_to_file: Whether to log to file
            log_level: Logging level
        """
        self.logger = Logger(log_to_file=log_to_file, log_level=log_level)
        self.storage_path = storage_path
        self.scheduled_file = os.path.join(storage_path, "scheduled_emails.json")
        self._ensure_storage_exists()
        self._worker_thread = None
        self._stop_worker = threading.Event()
        self.logger.info(f"EmailScheduler initialized with storage at {self.storage_path}")
    
    def _ensure_storage_exists(self):
        """Create storage directory if it doesn't exist."""
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
            self.logger.info(f"Created storage directory: {self.storage_path}")
        
        if not os.path.exists(self.scheduled_file):
            with open(self.scheduled_file, 'w') as f:
                json.dump([], f)
            self.logger.info(f"Created scheduled emails file: {self.scheduled_file}")
    
    def schedule_email(
        self,
        scheduled_time: datetime,
        recipients: List[TemplateModelType],
        email_field: str,
        template_data: Dict[str, Any],
        attachment_paths: Optional[List[str]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        cc_field: str = "cc",
        bcc_field: str = "bcc",
        attachment_field: str = "attachments",
        schedule_id: Optional[str] = None
    ) -> str:
        """
        Schedule an email to be sent at a specific time.
        
        Args:
            scheduled_time: When to send the email
            recipients: List of recipient objects
            email_field: Field name containing recipient email
            template_data: Template engine data (subject, body_text, body_html)
            attachment_paths: List of attachment file paths
            cc: List of CC email addresses
            bcc: List of BCC email addresses
            cc_field: Field name for CC in recipient object
            bcc_field: Field name for BCC in recipient object
            attachment_field: Field name for attachments in recipient object
            schedule_id: Optional custom ID for this scheduled email
            
        Returns:
            schedule_id: Unique identifier for this scheduled email
        """
        if scheduled_time <= datetime.now():
            self.logger.warning("Scheduled time is in the past. Email will be sent on the next worker cycle.")
        
        # Generate schedule ID if not provided
        if schedule_id is None:
            schedule_id = f"schedule_{int(time.time() * 1000)}"
        
        # Convert recipients to serializable format
        serialized_recipients = []
        for recipient in recipients:
            serialized_recipients.append(recipient.__dict__)
        
        scheduled_email = {
            "schedule_id": schedule_id,
            "scheduled_time": scheduled_time.isoformat(),
            "recipients": serialized_recipients,
            "email_field": email_field,
            "template_data": template_data,
            "attachment_paths": attachment_paths or [],
            "cc": cc or [],
            "bcc": bcc or [],
            "cc_field": cc_field,
            "bcc_field": bcc_field,
            "attachment_field": attachment_field,
            "status": "pending"
        }
        
        # Load existing schedules
        schedules = self._load_schedules()
        
        # Check if schedule_id already exists
        existing_ids = [s["schedule_id"] for s in schedules]
        if schedule_id in existing_ids:
            self.logger.error(f"Schedule ID {schedule_id} already exists")
            raise ValueError(f"Schedule ID {schedule_id} already exists")
        
        schedules.append(scheduled_email)
        self._save_schedules(schedules)
        
        self.logger.info(f"Scheduled email with ID {schedule_id} for {scheduled_time}")
        return schedule_id
    
    def cancel_schedule(self, schedule_id: str) -> bool:
        """
        Cancel a scheduled email.
        
        Args:
            schedule_id: ID of the scheduled email to cancel
            
        Returns:
            True if canceled successfully, False if not found
        """
        schedules = self._load_schedules()
        initial_count = len(schedules)
        
        schedules = [s for s in schedules if s["schedule_id"] != schedule_id]
        
        if len(schedules) < initial_count:
            self._save_schedules(schedules)
            self.logger.info(f"Canceled scheduled email with ID {schedule_id}")
            return True
        else:
            self.logger.warning(f"Schedule ID {schedule_id} not found")
            return False
    
    def get_scheduled_emails(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of scheduled emails.
        
        Args:
            status: Filter by status (pending, sent, failed). None returns all.
            
        Returns:
            List of scheduled email dictionaries
        """
        schedules = self._load_schedules()
        
        if status:
            schedules = [s for s in schedules if s.get("status") == status]
        
        return schedules
    
    def _load_schedules(self) -> List[Dict[str, Any]]:
        """Load schedules from file."""
        try:
            with open(self.scheduled_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_schedules(self, schedules: List[Dict[str, Any]]):
        """Save schedules to file."""
        with open(self.scheduled_file, 'w') as f:
            json.dump(schedules, f, indent=2)
    
    def start_worker(self, smartmailer_instance, check_interval: int = 60):
        """
        Start background worker to check and send scheduled emails.
        
        Args:
            smartmailer_instance: Instance of SmartMailer to use for sending
            check_interval: How often to check for scheduled emails (in seconds)
        """
        if self._worker_thread and self._worker_thread.is_alive():
            self.logger.warning("Worker thread is already running")
            return
        
        self._stop_worker.clear()
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            args=(smartmailer_instance, check_interval),
            daemon=True
        )
        self._worker_thread.start()
        self.logger.info(f"Started scheduler worker thread with {check_interval}s check interval")
    
    def stop_worker(self):
        """Stop the background worker."""
        if self._worker_thread and self._worker_thread.is_alive():
            self._stop_worker.set()
            self._worker_thread.join(timeout=5)
            self.logger.info("Stopped scheduler worker thread")
        else:
            self.logger.warning("Worker thread is not running")
    
    def _worker_loop(self, smartmailer_instance, check_interval: int):
        """Main worker loop that checks and sends scheduled emails."""
        from smartmailer.core.template import TemplateEngine, TemplateModel
        
        self.logger.info("Worker loop started")
        
        while not self._stop_worker.is_set():
            try:
                schedules = self._load_schedules()
                now = datetime.now()
                
                for schedule in schedules:
                    if schedule.get("status") != "pending":
                        continue
                    
                    scheduled_time = datetime.fromisoformat(schedule["scheduled_time"])
                    
                    if now >= scheduled_time:
                        self.logger.info(f"Sending scheduled email {schedule['schedule_id']}")
                        
                        try:
                            # Recreate recipient objects
                            recipients = []
                            for recipient_dict in schedule["recipients"]:
                                # Create a dynamic TemplateModel subclass
                                recipient_obj = TemplateModel(**recipient_dict)
                                recipients.append(recipient_obj)
                            
                            # Create template engine
                            template = TemplateEngine(
                                subject=schedule["template_data"].get("subject", ""),
                                body_text=schedule["template_data"].get("body_text"),
                                body_html=schedule["template_data"].get("body_html")
                            )
                            
                            # Send emails
                            smartmailer_instance.send_emails(
                                recipients=recipients,
                                email_field=schedule["email_field"],
                                template=template,
                                attachment_paths=schedule.get("attachment_paths"),
                                cc=schedule.get("cc"),
                                bcc=schedule.get("bcc"),
                                cc_field=schedule.get("cc_field", "cc"),
                                bcc_field=schedule.get("bcc_field", "bcc"),
                                attachment_field=schedule.get("attachment_field", "attachments")
                            )
                            
                            # Update status
                            schedule["status"] = "sent"
                            schedule["sent_at"] = datetime.now().isoformat()
                            self.logger.info(f"Successfully sent scheduled email {schedule['schedule_id']}")
                            
                        except Exception as e:
                            self.logger.error(f"Error sending scheduled email {schedule['schedule_id']}: {e}")
                            schedule["status"] = "failed"
                            schedule["error"] = str(e)
                        
                        # Save updated schedules
                        self._save_schedules(schedules)
                
            except Exception as e:
                self.logger.error(f"Error in worker loop: {e}")
            
            # Wait for check interval or stop event
            self._stop_worker.wait(timeout=check_interval)
        
        self.logger.info("Worker loop stopped")
