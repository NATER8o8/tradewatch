
from typing import Optional

async def send_email(to_email: str, subject: str, text: str, html: Optional[str]=None, model: dict=None) -> bool:
    print(f"EMAIL to={to_email} subject={subject}\n{text}")
    return True
