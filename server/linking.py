
from typing import Dict, Any, Optional
import re

MAP = {
    "finance": ["bank", "budget", "finance", "appropriation"],
    "technology": ["technology", "science", "ai", "cyber", "communications"],
    "energy": ["energy", "oil", "gas", "mining", "climate"],
    "healthcare": ["health", "medic", "pharma"],
    "defense": ["armed", "defense", "intelligence", "security"],
    "agriculture": ["agriculture", "farm"],
    "transportation": ["transport", "infrastructure", "aviation", "rail"],
}

def infer_sector_from_committees(committees: str) -> Optional[str]:
    s = committees.lower()
    for sector, keywords in MAP.items():
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", s):
                return sector
    return None
