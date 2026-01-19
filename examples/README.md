# SmartMailer Examples

This directory contains example scripts demonstrating the features of SmartMailer.

## Demo: New Features

**File:** `demo_new_features.py`

This comprehensive demo showcases the latest features added to SmartMailer:

### 1. Template Default Values

Provide fallback values for optional fields:
```python
template = TemplateEngine(
    subject="Welcome, {{ nickname|default:\"Friend\" }}!",
    body_text="Dear {{ nickname|default:\"Valued Customer\" }}, ..."
)
```

### 2. Conditional Rendering

Show/hide sections based on field values:
```python
body_text="""
{% if vip_status %}
🌟 VIP MEMBER BENEFITS 🌟
- Priority customer support
- Exclusive deals
{% endif %}
"""
```

### 3. Email Scheduling

Schedule emails to be sent at a future time:
```python
# Relative time
scheduled_time = EmailScheduler.parse_schedule_time("+2h")

# Absolute time
scheduled_time = EmailScheduler.parse_schedule_time("2025-12-25 14:30:00")

smartmailer.send_emails(
    recipients=recipients,
    email_field="email",
    template=template,
    scheduled_time=scheduled_time
)
```

## Running the Examples

```bash
# Run the new features demo
python examples/demo_new_features.py
```

The demo script doesn't require SMTP credentials as it only demonstrates template rendering and scheduling features without actually sending emails.

## Output

The demo will show:
- How default values are applied when fields are missing
- How conditional sections appear or disappear based on data
- How scheduling times are parsed and calculated
- Combined usage of all features together

## Additional Resources

- See [DOCS.md](../DOCS.md) for complete documentation
- See [README.md](../README.md) for an overview of SmartMailer
