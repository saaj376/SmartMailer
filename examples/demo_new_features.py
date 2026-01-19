"""
Example demonstrating the new SmartMailer features:
1. Template default values
2. Conditional rendering
3. Email scheduling

This is a demonstration script - it won't actually send emails without valid SMTP credentials.
"""

from datetime import datetime, timedelta
from typing import Optional
from smartmailer import SmartMailer, TemplateEngine, TemplateModel, EmailScheduler


# Define a schema with optional fields for demonstration
class UserNotification(TemplateModel):
    name: str
    email: str
    nickname: Optional[str] = None
    vip_status: Optional[bool] = None
    discount_code: Optional[str] = None
    account_balance: Optional[float] = None


def example_1_default_values():
    """Example 1: Using default values in templates"""
    print("\n=== Example 1: Template Default Values ===\n")
    
    # Create a template with default values
    template = TemplateEngine(
        subject="Welcome, {{ nickname|default:\"Friend\" }}!",
        body_text="""
Dear {{ nickname|default:"Valued Customer" }},

Thank you for joining us! We're excited to have {{ name }} as part of our community.

Best regards,
The Team
"""
    )
    
    # Create recipients - some with nicknames, some without
    recipients = [
        UserNotification(name="Alice Johnson", email="alice@example.com", nickname="Ally"),
        UserNotification(name="Bob Smith", email="bob@example.com", nickname=None),
        UserNotification(name="Charlie Brown", email="charlie@example.com"),
    ]
    
    # Render templates to see the results
    for recipient in recipients:
        rendered = template.render(recipient)
        print(f"To: {recipient.email}")
        print(f"Subject: {rendered['subject']}")
        print(f"Body: {rendered['text']}")
        print("-" * 50)


def example_2_conditional_rendering():
    """Example 2: Using conditional blocks in templates"""
    print("\n=== Example 2: Conditional Rendering ===\n")
    
    # Create a template with conditional sections
    template = TemplateEngine(
        subject="Your Account Status",
        body_text="""
Dear {{ name }},

Thank you for being a customer!

{% if vip_status %}
🌟 VIP MEMBER BENEFITS 🌟
As a VIP member, you enjoy:
- Priority customer support
- Exclusive deals and offers
- Early access to new features
{% endif %}

{% if discount_code %}
Use your exclusive discount code: {{ discount_code }}
{% endif %}

{% if account_balance %}
Your current account balance: ${{ account_balance }}
{% endif %}

Best regards,
The Team
"""
    )
    
    # Create recipients with different status
    recipients = [
        UserNotification(
            name="Alice VIP",
            email="alice@example.com",
            vip_status=True,
            discount_code="VIP2025",
            account_balance=150.50
        ),
        UserNotification(
            name="Bob Regular",
            email="bob@example.com",
            vip_status=False,
            discount_code=None,
            account_balance=None
        ),
    ]
    
    # Render templates to see the results
    for recipient in recipients:
        rendered = template.render(recipient)
        print(f"To: {recipient.email}")
        print(f"Body: {rendered['text']}")
        print("-" * 50)


def example_3_email_scheduling():
    """Example 3: Scheduling emails"""
    print("\n=== Example 3: Email Scheduling ===\n")
    
    # Parse different schedule formats
    print("Schedule time parsing examples:")
    
    # Relative time
    schedule_1 = EmailScheduler.parse_schedule_time("+2h")
    print(f"'+2h' parses to: {schedule_1}")
    
    schedule_2 = EmailScheduler.parse_schedule_time("+30m")
    print(f"'+30m' parses to: {schedule_2}")
    
    schedule_3 = EmailScheduler.parse_schedule_time("+1d")
    print(f"'+1d' parses to: {schedule_3}")
    
    # ISO format
    schedule_4 = EmailScheduler.parse_schedule_time("2025-12-25 14:30:00")
    print(f"'2025-12-25 14:30:00' parses to: {schedule_4}")
    
    # Calculate delays
    future_time = datetime.now() + timedelta(hours=2)
    delay = EmailScheduler.calculate_delay(future_time)
    print(f"\nDelay until {future_time}: {delay:.1f} seconds ({delay/3600:.2f} hours)")
    
    print("\n--- To actually send scheduled emails ---")
    print("""
# Example usage with SmartMailer:
from smartmailer import SmartMailer, EmailScheduler

scheduled_time = EmailScheduler.parse_schedule_time("+2h")

smartmailer = SmartMailer(
    sender_email="your_email@gmail.com",
    password="your_password",
    provider="gmail",
    session_name="scheduled_campaign"
)

smartmailer.send_emails(
    recipients=obj_recipients,
    email_field="email",
    template=template,
    scheduled_time=scheduled_time  # <-- Schedule for future delivery
)
""")


def example_4_combined_features():
    """Example 4: Combining all features"""
    print("\n=== Example 4: Combined Features ===\n")
    
    # Template with default values AND conditional rendering
    template = TemplateEngine(
        subject="Special Offer for {{ nickname|default:\"You\" }}!",
        body_text="""
Hi {{ nickname|default:"there" }},

We have exciting news for {{ name }}!

{% if vip_status %}
As a VIP member, you get an EXTRA 20% off our special offer!
{% endif %}

{% if discount_code %}
Your personalized discount code: {{ discount_code }}
{% endif %}

{% if account_balance %}
You can use your account balance of ${{ account_balance }} towards this purchase.
{% endif %}

This offer is available for a limited time only!

Best regards,
The Team
"""
    )
    
    recipient = UserNotification(
        name="Charlie Customer",
        email="charlie@example.com",
        nickname=None,  # Will use default
        vip_status=True,  # Will show VIP section
        discount_code="SAVE30",  # Will show code
        account_balance=None  # Won't show balance section
    )
    
    rendered = template.render(recipient)
    print(f"To: {recipient.email}")
    print(f"Subject: {rendered['subject']}")
    print(f"Body: {rendered['text']}")
    
    # Schedule for 1 hour from now
    scheduled_time = EmailScheduler.parse_schedule_time("+1h")
    print(f"\nWould be scheduled to send at: {scheduled_time}")


if __name__ == "__main__":
    print("=" * 60)
    print("SmartMailer New Features Demo")
    print("=" * 60)
    
    example_1_default_values()
    example_2_conditional_rendering()
    example_3_email_scheduling()
    example_4_combined_features()
    
    print("\n" + "=" * 60)
    print("Demo completed! All new features demonstrated.")
    print("=" * 60)
