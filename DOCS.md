# SmartMailer

## Introduction

This is a library that makes it easy to handle mass-emailing on a large scale.
The main purpose of this library is to streamline and standardize template usage, and to assist in crash recovery by incorporating state management.

## Usage

### Install the Library

The process is not as straightforward as "pip install smartmailer", and we're working on it!

Until then,

```shell
pip install sqlalchemy tabulate pydantic

pip install -i https://test.pypi.org/simple/ smartmailer==0.0.3
```

Or,

```shell
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ smartmailer
```

### Importing and Using the Library

```python
from smartmailer import SmartMailer, TemplateModel, TemplateEngine

```

After importing, we need to define a schema for our data model.
This MySchema class inherits from TemplateModel.

(It's like defining a `Pydantic` model from its `BaseModel` class!)

We have four fields for this example. These four fields will be all we need to build the metadata for our email.

**NOTE**: Make sure to have a field for the **destination email address** (`email` here), as that will be used for the internal email logic.
You will use this as the `sender_email` argument when calling `send_emails`.

```python
class MySchema(TemplateModel):
    name: str
    committee: str
    allotment: str
    email: str
    
```

Next up, we define the templates for our subject and body.

### Defining Templates

- Template variables can be defined by wrapping the variable name with **Double Curly Braces**
- For example, `{{ name }}` is a variable with key "name".
- This variable name corresponds to the `MySchema` field you defined previously.
- Whitespaces between the variable name and the curly braces are optional, but we recommend them for better readability.

**NOTE**: Variable names must consist of either **lowercase alphanumeric characters, or underscore**. No other character is allowed.

Now, let's define the templates for the subject and body in these two files:

`subject.txt`:

```text
MUN Allotment Details
```

`body.txt`:

```text
Dear {{ name }},
Congratulations!! 
You are assigned to the {{ committee }} committee with the allotment of {{ allotment }}.
Regards,
The Organizing Committee
```

Let's load them into string objects, and initialize our Template Engine with the required data.

```python
with open("body.txt", "r") as f:
    body = f.read()

with open("subject.txt", "r") as f:
    subject = f.read()

template = TemplateEngine(subject=subject, body_text=body)
```

## Loading Data

The list of recipients is expected to be a list of `MySchema` objects, where we defined `MySchema` previously.
From whatever data source you have, convert the data into the schema that you defined.

In this example, my datasource is a list of dictionaries, for convenience.

```python
recipients = [
    {"name": "John", "committee": "ECOSOC", "allotment": "Algeria", "email": "myEmail@gmail.com"},
    {"name": "John", "committee": "ECOSOC", "allotment": "Algeria", "email": "myEmail@outlook.com"},
    {"name": "John", "committee": "ECOSOC", "allotment": "Algeria", "email": "myEmail@snuchennai.edu.in"},
]

obj_recipients = [MySchema(name=recipient['name'], committee=recipient['country'], allotment=recipient['allotment'], email= recipient['email'])  for recipient in recipients]
```

### Sending the Emails

Next, we define the SmartMailer instance which handles the email-sending for these recipients.
We need to provide the source email credentials, as well as the email provider to be used.

Currently supported options are: `"gmail"` and `"outlook"`. (case sensitive).

```python
smartmailer = SmartMailer(
    sender_email="myEmail@gmail.com",
    password="myPass",
    provider="gmail",
    session_name="test"
)
```

After that's done, all that's left is to send the emails.

```python
smartmailer.send_emails(
    recipients=obj_recipients,
    email_field="email",
    template=template
)
```

And we're done!

## Adding CC, BCC, and Attachments

Sometimes, you might want to send emails with CC, BCC, or include attachments. SmartMailer makes this easy — just add the relevant fields to your schema and pass the field names to `send_emails`.

First, update your schema to include optional fields for `cc`, `bcc`, and `attachments`:

```python
from typing import List, Optional

class MySchema(TemplateModel):
    name: str
    committee: str
    allotment: str
    email: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
```

When preparing your recipient data, you can now include these fields:

```python
recipients = [
    {
        "name": "Arjun",
        "committee": "UNDP",
        "allotment": "India",
        "email": "arjun@example.com",
        "cc": ["ccperson@example.com"],
        "bcc": ["bccperson@example.com"],
        "attachments": [r"C:\path\to\file.pdf"]
    },
    # ... more recipients ...
]

obj_recipients = [
    MySchema(
        name=recipient['name'],
        committee=recipient['committee'],
        allotment=recipient['allotment'],
        email=recipient['email'],
        cc=recipient.get('cc'),
        bcc=recipient.get('bcc'),
        attachments=recipient.get('attachments')
    )
    for recipient in recipients
]
```

When calling `send_emails`, just specify the field names for CC, BCC, and attachments:

```python
smartmailer.send_emails(
    recipients=obj_recipients,
    email_field="email",
    template=template,
    cc_field="cc",
    bcc_field="bcc",
    attachment_field="attachments"
)
```

That's it! Your emails will now include CC, BCC, and any attachments (all file types supported) you specify for each recipient.

## Email Scheduling

SmartMailer includes an email scheduler that allows you to schedule emails to be sent at a specific time in the future. This is useful for planning campaigns, sending reminders, or automating email workflows.

### Basic Scheduling

To schedule emails, use the `schedule_emails` method which works similarly to `send_emails` but with an additional `scheduled_time` parameter:

```python
from datetime import datetime, timedelta
from smartmailer import SmartMailer, TemplateModel, TemplateEngine

# Initialize SmartMailer
smartmailer = SmartMailer(
    sender_email="myEmail@gmail.com",
    password="myPass",
    provider="gmail",
    session_name="scheduled_campaign"
)

# Create recipients and template
class MySchema(TemplateModel):
    name: str
    email: str

recipients = [
    MySchema(name="Alice", email="alice@example.com"),
    MySchema(name="Bob", email="bob@example.com")
]

template = TemplateEngine(
    subject="Scheduled Email",
    body_text="Hello {{ name }}, this is a scheduled email!"
)

# Schedule emails to be sent 2 hours from now
scheduled_time = datetime.now() + timedelta(hours=2)

schedule_id = smartmailer.schedule_emails(
    scheduled_time=scheduled_time,
    recipients=recipients,
    email_field="email",
    template=template
)

print(f"Emails scheduled with ID: {schedule_id}")
```

### Using the EmailScheduler Directly

For more advanced control, you can use the `EmailScheduler` class directly:

```python
from datetime import datetime, timedelta
from smartmailer import SmartMailer, EmailScheduler, TemplateModel, TemplateEngine

# Create scheduler
scheduler = EmailScheduler(storage_path="my_scheduled_emails")

# Schedule emails
schedule_id = scheduler.schedule_email(
    scheduled_time=datetime.now() + timedelta(days=1),
    recipients=recipients,
    email_field="email",
    template_data={
        "subject": "Scheduled Subject",
        "body_text": "Hello {{ name }}",
        "body_html": "<p>Hello {{ name }}</p>"
    }
)

# View all scheduled emails
scheduled = scheduler.get_scheduled_emails(status="pending")
for email in scheduled:
    print(f"Schedule ID: {email['schedule_id']}, Time: {email['scheduled_time']}")

# Cancel a scheduled email
scheduler.cancel_schedule(schedule_id)
```

### Running the Scheduler Worker

To automatically send scheduled emails, you need to start a background worker:

```python
# Initialize SmartMailer
smartmailer = SmartMailer(
    sender_email="myEmail@gmail.com",
    password="myPass",
    provider="gmail",
    session_name="automated_session"
)

# Create and start scheduler
scheduler = EmailScheduler()

# Start the worker (checks every 60 seconds by default)
scheduler.start_worker(smartmailer, check_interval=60)

# Keep your application running...
# The worker will automatically send scheduled emails when their time comes

# When you're done:
scheduler.stop_worker()
```

### Scheduled Email Features

- **Persistent Storage**: Scheduled emails are stored in JSON files and persist across application restarts
- **Status Tracking**: Track whether emails are pending, sent, or failed
- **Flexible Scheduling**: Schedule emails for any future date and time
- **Attachments & CC/BCC**: Full support for attachments, CC, and BCC in scheduled emails
- **Background Worker**: Automated background worker to send emails at the right time
- **Cancellation**: Cancel scheduled emails before they are sent
