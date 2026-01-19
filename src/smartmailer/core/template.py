from typing import Optional, Dict, Any
from pydantic import BaseModel, model_validator, computed_field
import re
import json

def get_placeholder_regex(key) -> re.Pattern:
    pattern = r"\{\{ *KEY *\}\}".replace("KEY", key)
    return re.compile(pattern)

def get_placeholder_with_default_regex(key) -> re.Pattern:
    """Matches {{ key|default:"value" }} or {{ key | default : "value" }}"""
    pattern = r'\{\{ *KEY *\| *default *: *"([^"]*)" *\}\}'.replace("KEY", key)
    return re.compile(pattern)

def get_conditional_block_regex(key) -> re.Pattern:
    """Matches {% if key %}...{% endif %}"""
    pattern = r'\{% *if *KEY *%\}(.*?)\{% *endif *%\}'.replace("KEY", key)
    return re.compile(pattern, re.DOTALL)

class TemplateModel(BaseModel):
    @model_validator(mode='after')
    def check_lowercase_alphanumeric(self):
        # we are validating the field names themselves, not the value.
        # this is because we are replacing them in the template string.
        for name, _ in self.__dict__.items():
            if not re.fullmatch(r'[a-z0-9_]+', name):
                raise ValueError(f"Field '{name}' must be lowercase alphanumeric characters or underscore.")
        return self

    @computed_field
    @property
    def hash_string(self) -> str:
        """
        Returns a hash of the model's fields.
        This is used to uniquely identify the template model.
        """
        # we cant do model_dump because it keeps recursively calling this computed field
        dump = self.model_json_schema()
        res = {}
        for key in dump["properties"].keys():
            res[key] = self.__dict__.get(key, None)
        return json.dumps(res)

class TemplateEngine:
    subject: Optional[str] = None
    text: Optional[str] = None
    html: Optional[str] = None

    def __init__(self, subject: Optional[str] = None, body_text: Optional[str] = None, body_html: Optional[str] = None):
        self.subject = subject
        self.text = body_text
        self.html = body_html

    def render(self, fields: TemplateModel) -> Dict[str, str]:
        res: dict = {
            "subject": self.subject,
            "text": self.text,
            "html": self.html
        }

        field_dict = fields.model_dump()
        
        # First pass: Handle conditional blocks
        for key, value in field_dict.items():
            conditional_regex = get_conditional_block_regex(key)
            
            if self.subject:
                # If field has a truthy value, keep the content; otherwise remove the block
                if value:
                    res["subject"] = conditional_regex.sub(r'\1', res["subject"])
                else:
                    res["subject"] = conditional_regex.sub('', res["subject"])
            if self.text:
                if value:
                    res["text"] = conditional_regex.sub(r'\1', res["text"])
                else:
                    res["text"] = conditional_regex.sub('', res["text"])
            if self.html:
                if value:
                    res["html"] = conditional_regex.sub(r'\1', res["html"])
                else:
                    res["html"] = conditional_regex.sub('', res["html"])

        # Second pass: Handle placeholders with default values
        for key, value in field_dict.items():
            default_regex = get_placeholder_with_default_regex(key)
            
            # If value is None or empty, use the default value; otherwise use the actual value
            def replace_with_default(match):
                default_value = match.group(1)
                return str(value) if value else default_value
            
            if self.subject:
                res["subject"] = default_regex.sub(replace_with_default, res["subject"])
            if self.text:
                res["text"] = default_regex.sub(replace_with_default, res["text"])
            if self.html:
                res["html"] = default_regex.sub(replace_with_default, res["html"])

        # Third pass: Handle regular placeholders
        for key, value in field_dict.items():
            regex = get_placeholder_regex(key)

            if self.subject:
                res["subject"] = regex.sub(str(value), res["subject"])
            if self.text:
                res["text"] = regex.sub(str(value), res["text"])
            if self.html:
                res["html"] = regex.sub(str(value), res["html"])

        return res
