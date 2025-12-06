# # invoice_qc/extractor.py
# from __future__ import annotations

# from pathlib import Path
# from typing import List, Optional
# import re

# import pdfplumber

# from .schema import Invoice, LineItem
# from .utils.helpers import parse_amount, parse_date


# # INVOICE_NUMBER_PATTERNS = [
# #     r"Invoice\s*(No\.?|Number|#)\s*[:\-]?\s*(\S+)",
# #     r"Inv\.\s*No\.?\s*[:\-]?\s*(\S+)",
# # ]

# INVOICE_NUMBER_PATTERNS += [
#     r"Bestellung\s+([A-Z0-9]+)",
#     r"AUFNR\s*([A-Z0-9]+)"
# ]


# # INVOICE_DATE_PATTERNS = [
# #     r"Invoice\s*Date\s*[:\-]?\s*([0-9./-]+)",
# #     r"Date\s*[:\-]?\s*([0-9./-]+)",
# # ]

# NET_TOTAL_PATTERNS += [
#     r"Gesamtwert\s*EUR\s*([0-9,.\s]+)"
# ]

# TAX_PATTERNS += [
#     r"MwSt.*EUR\s*([0-9,.\s]+)"
# ]

# GROSS_TOTAL_PATTERNS += [
#     r"Gesamtwert\s*inkl\.\s*MwSt\.\s*EUR\s*([0-9,.\s]+)"
# ]


# DUE_DATE_PATTERNS = [
#     r"Due\s*Date\s*[:\-]?\s*([0-9./-]+)",
#     r"Payment\s*Due\s*[:\-]?\s*([0-9./-]+)",
# ]

# CURRENCY_PATTERNS = [
#     r"Currency\s*[:\-]?\s*([A-Z]{3})",
#     r"\b(INR|EUR|USD|GBP)\b",
# ]

# NET_TOTAL_PATTERNS = [
#     r"(Subtotal|Net\s*Total|Net\s*Amount)\s*[:\-]?\s*([0-9,.\s₹$€]+)",
# ]

# TAX_PATTERNS = [
#     r"(Tax|GST|VAT)\s*[:\-]?\s*([0-9,.\s₹$€]+)",
# ]

# GROSS_TOTAL_PATTERNS = [
#     r"(Total\s*Amount\s*Payable|Grand\s*Total|Total)\s*[:\-]?\s*([0-9,.\s₹$€]+)",
# ]


# def _extract_text(pdf_path: Path) -> str:
#     parts = []
#     with pdfplumber.open(str(pdf_path)) as pdf:
#         for page in pdf.pages:
#             text = page.extract_text() or ""
#             parts.append(text)
#     return "\n".join(parts)


# def _search_first(patterns, text: str, group_index: int = 1) -> Optional[str]:
#     for pat in patterns:
#         m = re.search(pat, text, flags=re.IGNORECASE)
#         if m:
#             return m.group(group_index).strip()
#     return None


# def _extract_invoice_number(text: str) -> Optional[str]:
#     return _search_first(INVOICE_NUMBER_PATTERNS, text, group_index=2)


# def _extract_invoice_date(text: str) -> Optional[str]:
#     raw = _search_first(INVOICE_DATE_PATTERNS, text, group_index=1)
#     return parse_date(raw) if raw else None


# def _extract_due_date(text: str) -> Optional[str]:
#     raw = _search_first(DUE_DATE_PATTERNS, text, group_index=1)
#     return parse_date(raw) if raw else None


# def _extract_currency(text: str) -> Optional[str]:
#     raw = _search_first(CURRENCY_PATTERNS, text, group_index=1)
#     return raw if raw else None


# def _extract_amount(patterns, text: str) -> Optional[float]:
#     raw = _search_first(patterns, text, group_index=2)
#     return parse_amount(raw) if raw else None


# def _extract_parties(text: str) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
#     """
#     Very simple heuristic:
#     - Look for 'Seller'/'Supplier' and 'Buyer'/'Bill To'.
#     - Next non-empty line treated as name, next line as address.
#     - Tax ID line containing GST/VAT/PAN/etc.
#     """
#     lines = [l.strip() for l in text.splitlines()]
#     seller_name = seller_addr = seller_tax_id = None
#     buyer_name = buyer_addr = buyer_tax_id = None

#     def find_block(keyword_list):
#         for idx, line in enumerate(lines):
#             if any(k.lower() in line.lower() for k in keyword_list):
#                 # next one or two lines are details
#                 name = None
#                 addr = None
#                 tax_id = None
#                 for j in range(1, 5):
#                     if idx + j >= len(lines):
#                         break
#                     candidate = lines[idx + j]
#                     if not candidate:
#                         continue
#                     # tax id-ish
#                     if re.search(r"(GST|VAT|PAN|TIN|Tax\s*ID)", candidate, re.IGNORECASE):
#                         tax_id = candidate
#                     elif name is None:
#                         name = candidate
#                     elif addr is None:
#                         addr = candidate
#                 return name, addr, tax_id
#         return None, None, None

#     seller_name, seller_addr, seller_tax_id = find_block(["Seller", "Supplier", "From"])
#     buyer_name, buyer_addr, buyer_tax_id = find_block(["Buyer", "Bill To", "Ship To", "Customer"])

#     return seller_name, seller_addr, seller_tax_id, buyer_name, buyer_addr, buyer_tax_id


# def _extract_line_items(text: str) -> list[LineItem]:
#     """
#     Heuristic line-item extraction:
#     - Find a header line containing 'Description' and 'Qty' and 'Rate/Price' and 'Amount/Total'.
#     - After that, parse lines that look like: desc ... qty ... unit ... total
#     """
#     lines = [l for l in text.splitlines()]
#     items: list[LineItem] = []

#     header_idx = None
#     for i, line in enumerate(lines):
#         low = line.lower()
#         if "description" in low and ("qty" in low or "quantity" in low) and ("rate" in low or "price" in low) and ("amount" in low or "total" in low):
#             header_idx = i
#             break

#     if header_idx is None:
#         return items

#     data_lines = lines[header_idx + 1 :]

#     pattern = re.compile(
#         r"^(?P<desc>.+?)\s+(?P<qty>\d+(?:\.\d+)?)\s+(?P<unit>\d+(?:\.\d+)?)\s+(?P<total>\d+(?:\.\d+)?)\s*$"
#     )

#     for line in data_lines:
#         line = line.strip()
#         if not line:
#             continue
#         m = pattern.match(line)
#         if not m:
#             continue
#         desc = m.group("desc").strip()
#         qty = parse_amount(m.group("qty"))
#         unit_price = parse_amount(m.group("unit"))
#         total = parse_amount(m.group("total"))
#         items.append(
#             LineItem(
#                 description=desc,
#                 quantity=qty,
#                 unit_price=unit_price,
#                 line_total=total,
#             )
#         )

#     return items


# def extract_invoice_from_pdf(pdf_path: Path) -> Invoice:
#     text = _extract_text(pdf_path)

#     inv_number = _extract_invoice_number(text)
#     inv_date = _extract_invoice_date(text)
#     due_date = _extract_due_date(text)
#     currency = _extract_currency(text)

#     net_total = _extract_amount(NET_TOTAL_PATTERNS, text)
#     tax_amount = _extract_amount(TAX_PATTERNS, text)
#     gross_total = _extract_amount(GROSS_TOTAL_PATTERNS, text)

#     (
#         seller_name,
#         seller_addr,
#         seller_tax_id,
#         buyer_name,
#         buyer_addr,
#         buyer_tax_id,
#     ) = _extract_parties(text)

#     line_items = _extract_line_items(text)

#     return Invoice(
#         invoice_number=inv_number,
#         invoice_date=inv_date,
#         due_date=due_date,
#         seller_name=seller_name,
#         seller_address=seller_addr,
#         seller_tax_id=seller_tax_id,
#         buyer_name=buyer_name,
#         buyer_address=buyer_addr,
#         buyer_tax_id=buyer_tax_id,
#         currency=currency,
#         net_total=net_total,
#         tax_amount=tax_amount,
#         gross_total=gross_total,
#         line_items=line_items,
#         source_pdf=pdf_path.name,
#     )


# def extract_invoices_from_dir(pdf_dir: Path) -> List[Invoice]:
#     invoices: List[Invoice] = []
#     for path in sorted(pdf_dir.glob("*.pdf")):
#         invoices.append(extract_invoice_from_pdf(path))
#     return invoices

from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import re
import pdfplumber

from .schema import Invoice, LineItem
from .utils.helpers import parse_amount, parse_date


"""
----------------------------------------------------
  1) BASE REGEX PATTERNS (English/Generic)
----------------------------------------------------
"""
INVOICE_NUMBER_PATTERNS = [
    r"Invoice\s*(No\.?|Number|#)\s*[:\-]?\s*(\S+)",
    r"Inv\.\s*No\.?\s*[:\-]?\s*(\S+)",
]

INVOICE_DATE_PATTERNS = [
    r"Invoice\s*Date\s*[:\-]?\s*([0-9./-]+)",
    r"Date\s*[:\-]?\s*([0-9./-]+)",
]

DUE_DATE_PATTERNS = [
    r"Due\s*Date\s*[:\-]?\s*([0-9./-]+)",
    r"Payment\s*Due\s*[:\-]?\s*([0-9./-]+)",
]

CURRENCY_PATTERNS = [
    r"Currency\s*[:\-]?\s*([A-Z]{3})",
    r"\b(INR|EUR|USD|GBP)\b",
]

NET_TOTAL_PATTERNS = [
    r"(Subtotal|Net\s*Total|Net\s*Amount)\s*[:\-]?\s*([0-9,.\s₹$€]+)",
]

TAX_PATTERNS = [
    r"(Tax|GST|VAT)\s*[:\-]?\s*([0-9,.\s₹$€]+)",
]

GROSS_TOTAL_PATTERNS = [
    r"(Total\s*Amount\s*Payable|Grand\s*Total|Total)\s*[:\-]?\s*([0-9,.\s₹$€]+)",
]


"""
----------------------------------------------------
  2) ADD GERMAN INVOICE PATTERNS
----------------------------------------------------
"""
# Bestellung AUFNR34343
INVOICE_NUMBER_PATTERNS += [
    r"Bestellung\s+(AUFNR[0-9A-Za-z]+)",
    r"AUFNR\s*([A-Z0-9]+)"
]

# e.g. "vom 22.05.2024"
INVOICE_DATE_PATTERNS += [
    r"vom\s*([0-9]{2}\.[0-9]{2}\.[0-9]{4})"
]

# Gesamtwert / MwSt 19% / inkl. MwSt
NET_TOTAL_PATTERNS += [
    r"Gesamtwert\s*EUR\s*([0-9,.\s]+)"
]

TAX_PATTERNS += [
    r"MwSt.*EUR\s*([0-9,.\s]+)"
]

GROSS_TOTAL_PATTERNS += [
    r"Gesamtwert\s*inkl\.\s*MwSt\.\s*EUR\s*([0-9,.\s]+)"
]


"""
----------------------------------------------------
  3) EXTRACTION HELPERS
----------------------------------------------------
"""
def _extract_text(pdf_path: Path) -> str:
    parts = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            parts.append(text)
    return "\n".join(parts)


def _search_first(patterns, text: str, group_index: int = 1) -> Optional[str]:
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return m.group(group_index).strip()
    return None


def _extract_invoice_number(text: str) -> Optional[str]:
    return _search_first(INVOICE_NUMBER_PATTERNS, text, group_index=1)


def _extract_invoice_date(text: str) -> Optional[str]:
    raw = _search_first(INVOICE_DATE_PATTERNS, text, group_index=1)
    return parse_date(raw) if raw else None


def _extract_due_date(text: str) -> Optional[str]:
    raw = _search_first(DUE_DATE_PATTERNS, text, group_index=1)
    return parse_date(raw) if raw else None


def _extract_currency(text: str) -> Optional[str]:
    raw = _search_first(CURRENCY_PATTERNS, text, group_index=1)
    return raw if raw else None


def _extract_amount(patterns, text: str) -> Optional[float]:
    raw = _search_first(patterns, text, group_index=1)
    return parse_amount(raw) if raw else None


# def _extract_parties(text: str):
#     """
#     Simple heuristic for German/Generic:
#     Try to detect seller at top, buyer near 'Kundenanschrift'.
#     """
#     lines = [l.strip() for l in text.splitlines()]
#     seller_name = None
#     buyer_name = None

#     # Seller = first non-empty line with a company-like name
#     for l in lines[:5]:
#         if re.search(r"[A-Za-z]{3,}", l) and "Seite" not in l and "Bestellung" not in l:
#             seller_name = l
#             break

#     # Buyer = line after "Kundenanschrift"
#     for i, l in enumerate(lines):
#         if "Kundenanschrift" in l:
#             if i+1 < len(lines):
#                 buyer_name = lines[i+1].strip()
#             break

#     return seller_name, None, None, buyer_name, None, None


# def _extract_parties(text: str):
#     """
#     Extract seller and buyer name + address blocks for German invoices.
#     """
#     lines = [l.strip() for l in text.splitlines() if l.strip()]

#     # --- Find seller block (top company) ---
#     seller_name = None
#     seller_addr = None

#     # First company-like name (ignore headers like "Seite 1 von 1")
#     for i, line in enumerate(lines):
#         if (
#             len(line) > 5 
#             and not line.lower().startswith("seite")
#             and not line.lower().startswith("bestellung")
#         ):
#             seller_name = line
#             # collect next lines until blank or anything numeric
#             addr = []
#             for l in lines[i+1:i+6]:
#                 if re.search(r"\d{5}", l) or re.search(r"\d", l) or "," in l:
#                     addr.append(l)
#                 elif any(w in l.lower() for w in ["kunde", "kundenanschrift"]):
#                     break
#                 else:
#                     addr.append(l)
#             seller_addr = ", ".join(addr) if addr else None
#             break

#     # --- Find buyer block (after Kundenanschrift) ---
#     buyer_name = None
#     buyer_addr = None
#     for i, line in enumerate(lines):
#         if "kundenanschrift" in line.lower():
#             # next non-empty line is buyer name
#             if i + 1 < len(lines):
#                 buyer_name = lines[i+1]
#             # collect address lines
#             addr = []
#             for l in lines[i+2:i+7]:
#                 if not l or "liefer" in l.lower() or "zahlungen" in l.lower():
#                     break
#                 addr.append(l)
#             buyer_addr = ", ".join(addr) if addr else None
#             break

#     return seller_name, seller_addr, None, buyer_name, buyer_addr, None

def _extract_parties(text: str):
    """
    Extract clean seller & buyer name/address blocks from German invoices.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Utility to clean repeated commas/spaces
    def clean_addr(addr):
        if not addr:
            return None
        return ", ".join(dict.fromkeys([a.strip(", ") for a in addr if a.strip()]))

    # --- SELLER NAME ---
    seller_name = None
    for line in lines:
        if "bestellung" in line.lower():
            # seller name is text before "Bestellung"
            parts = line.split("Bestellung", 1)
            if parts and parts[0].strip():
                seller_name = parts[0].strip()
            break

    # If seller not found from Bestellung, fallback to first company-like line
    if not seller_name:
        for line in lines:
            if len(line) >= 4 and not line.lower().startswith(("seite", "bestellung")):
                seller_name = line.strip()
                break

    # --- SELLER ADDRESS ---
    seller_addr = []
    start_collect = False
    for line in lines:
        if seller_name and seller_name in line:
            start_collect = True
            continue
        if start_collect:
            if "kundenanschrift" in line.lower():
                break
            seller_addr.append(line)

    seller_addr = clean_addr(seller_addr)

    # --- BUYER NAME & ADDRESS (AFTER 'KUNDENANSCHRIFT') ---
    buyer_name = None
    buyer_addr = []
    for i, line in enumerate(lines):
        if "kundenanschrift" in line.lower():
            if i + 1 < len(lines):
                buyer_name = lines[i + 1].strip()
            for l in lines[i + 2 : i + 10]:
                if "liefer" in l.lower() or "zahlung" in l.lower():
                    break
                buyer_addr.append(l)
            break

    # buyer_addr = clean_addr(buyer_addr)
    # Remove unwanted trailing info from buyer address
    if buyer_addr:
        filtered = []
        for l in buyer_addr:
            low = l.lower()
            if any(bad in low for bad in ["fax", "telefon", "bestellung", "kundennummer", "einkäufer"]):
                continue
            filtered.append(l)
        buyer_addr = clean_addr(filtered)
    else:
        buyer_addr = None


    return seller_name, seller_addr, None, buyer_name, buyer_addr, None


def _extract_line_items(text: str) -> list[LineItem]:
    """
    Very simplified version.
    """
    lines = [l for l in text.splitlines()]
    items: List[LineItem] = []

    # Only extract totals for now, because table layout varies highly
    return items


"""
----------------------------------------------------
  4) MAIN EXTRACT FUNCTION
----------------------------------------------------
"""
def extract_invoice_from_pdf(pdf_path: Path) -> Invoice:
    text = _extract_text(pdf_path)

    inv_number = _extract_invoice_number(text)
    inv_date = _extract_invoice_date(text)
    due_date = _extract_due_date(text)
    currency = _extract_currency(text)

    net_total = _extract_amount(NET_TOTAL_PATTERNS, text)
    tax_amount = _extract_amount(TAX_PATTERNS, text)
    gross_total = _extract_amount(GROSS_TOTAL_PATTERNS, text)

    (
        seller_name,
        seller_addr,
        seller_tax_id,
        buyer_name,
        buyer_addr,
        buyer_tax_id,
    ) = _extract_parties(text)

    # line items skipped for now (bonus if time)
    line_items = _extract_line_items(text)

    return Invoice(
        invoice_number=inv_number,
        invoice_date=inv_date,
        due_date=due_date,
        seller_name=seller_name,
        seller_address=seller_addr,
        seller_tax_id=seller_tax_id,
        buyer_name=buyer_name,
        buyer_address=buyer_addr,
        buyer_tax_id=buyer_tax_id,
        currency=currency,
        net_total=net_total,
        tax_amount=tax_amount,
        gross_total=gross_total,
        line_items=line_items,
        source_pdf=pdf_path.name,
    )


def extract_invoices_from_dir(pdf_dir: Path) -> List[Invoice]:
    invoices: List[Invoice] = []
    for path in sorted(pdf_dir.glob("*.pdf")):
        invoices.append(extract_invoice_from_pdf(path))
    return invoices
