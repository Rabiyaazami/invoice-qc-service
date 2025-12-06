import re
from typing import Optional
from dateutil import parser as dateparser

def parse_amount(raw: str) -> Optional[float]:
    if not raw:
        return None

    cleaned = raw.strip()

    cleaned = re.sub(r"[€$₹%]", "", cleaned)
    cleaned = cleaned.replace("EUR", "").replace("INR", "").replace("USD", "").strip()

    cleaned = cleaned.replace(" ", "")

    if re.match(r"^\d{1,3}(\.\d{3})+,\d{2}$", cleaned):
        cleaned = cleaned.replace(".", "")

    if "," in cleaned:
        cleaned = cleaned.replace(",", ".")

    cleaned = cleaned.replace(",", "").replace("’", "")

    try:
        return float(cleaned)
    except:
        return None

def parse_date(raw: str) -> Optional[str]:
    """
    Try to parse a date and return ISO string (YYYY-MM-DD).
    """
    if not raw:
        return None
    try:
        dt = dateparser.parse(raw, dayfirst=True)
        if dt.year < 2000 or dt.year > 2100:
            return None
        return dt.date().isoformat()
    except Exception:
        return None


def approx_equal(a: Optional[float], b: Optional[float], tolerance: float = 0.01) -> bool:
    if a is None or b is None:
        return False
    return abs(a - b) <= tolerance
