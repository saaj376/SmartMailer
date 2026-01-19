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

    def _apply_to_templates(self, res: dict, operation) -> None:
        """Helper to apply an operation to all non-None templates."""
        for field in ['subject', 'text', 'html']:
            if res[field]:
                res[field] = operation(res[field], field)
    
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
            
            def apply_conditional(template_content, field_name):
                # If field has a truthy value, keep the content; otherwise remove the block
                if value:
                    return conditional_regex.sub(r'\1', template_content)
                else:
                    return conditional_regex.sub('', template_content)
            
            self._apply_to_templates(res, apply_conditional)

        # Define the replacement function outside the loop
        def create_default_replacer(value):
            def replace_with_default(match):
                default_value = match.group(1)
                return str(value) if value else default_value
            return replace_with_default

        # Second pass: Handle placeholders with default values
        for key, value in field_dict.items():
            default_regex = get_placeholder_with_default_regex(key)
            replacer = create_default_replacer(value)
            
            def apply_default(template_content, field_name):
                return default_regex.sub(replacer, template_content)
            
            self._apply_to_templates(res, apply_default)

        # Third pass: Handle regular placeholders
        for key, value in field_dict.items():
            regex = get_placeholder_regex(key)
            
            def apply_placeholder(template_content, field_name):
                return regex.sub(str(value), template_content)
            
            self._apply_to_templates(res, apply_placeholder)

        return res
