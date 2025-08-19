
from typing import List, Dict, Any
from jinja2 import Template
from .email_service import send_email

TEMPLATE = Template("""Subject: {{ subject }}
Hi,
Here are your latest signals:

{% for it in items -%}
- {{ it['title'] }} — {{ it['value'] }}
{% endfor %}

— Official Trades Pro
""")

async def send_digest(to_email: str, items: List[Dict[str, Any]], subject: str = "Your OTP digest"):
    body = TEMPLATE.render(subject=subject, items=items)
    await send_email(to_email, subject, body)
