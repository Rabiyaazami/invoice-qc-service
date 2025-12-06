from __future__ import annotations

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    line_total: Optional[float] = None


class Invoice(BaseModel):
    # Core identifiers
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None  
    due_date: Optional[str] = None

    # Parties
    seller_name: Optional[str] = None
    seller_address: Optional[str] = None
    seller_tax_id: Optional[str] = None

    buyer_name: Optional[str] = None
    buyer_address: Optional[str] = None
    buyer_tax_id: Optional[str] = None

    # Money
    currency: Optional[str] = None
    net_total: Optional[float] = None
    tax_amount: Optional[float] = None
    gross_total: Optional[float] = None

    # Line items
    line_items: List[LineItem] = Field(default_factory=list)

    # Metadata
    source_pdf: Optional[str] = None  

class InvoiceValidationResult(BaseModel):
    invoice_id: str
    is_valid: bool
    errors: List[str]


class ValidationSummary(BaseModel):
    total_invoices: int
    valid_invoices: int
    invalid_invoices: int
    error_counts: Dict[str, int]
    invoices: List[InvoiceValidationResult]
