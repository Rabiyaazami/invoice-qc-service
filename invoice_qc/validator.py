from __future__ import annotations

from collections import Counter
from datetime import date
from typing import List, Tuple, Dict

from dateutil import parser as dateparser

from .schema import Invoice, InvoiceValidationResult, ValidationSummary
from .utils.helpers import approx_equal


ALLOWED_CURRENCIES = {"INR", "EUR", "USD", "GBP"}


def _parse_date_safe(d: str) -> date | None:
    if not d:
        return None
    try:
        return dateparser.parse(d).date()
    except Exception:
        return None


def validate_single_invoice(
    inv: Invoice,
    seen_keys: Dict[Tuple[str, str, str], int],
) -> InvoiceValidationResult:
    errors: List[str] = []

    if not inv.invoice_number:
        errors.append("missing_field: invoice_number")
    if not inv.invoice_date:
        errors.append("missing_field: invoice_date")
    if not inv.seller_name:
        errors.append("missing_field: seller_name")
    if not inv.buyer_name:
        errors.append("missing_field: buyer_name")

    if inv.currency and inv.currency not in ALLOWED_CURRENCIES:
        errors.append("format_error: currency_not_allowed")

    inv_date_obj = _parse_date_safe(inv.invoice_date) if inv.invoice_date else None
    due_date_obj = _parse_date_safe(inv.due_date) if inv.due_date else None

    if inv.invoice_date and not inv_date_obj:
        errors.append("format_error: invalid_invoice_date")
    if inv.due_date and not due_date_obj:
        errors.append("format_error: invalid_due_date")

    # reasonable date range
    if inv_date_obj:
        if inv_date_obj.year < 2000 or inv_date_obj.year > 2100:
            errors.append("format_error: invoice_date_out_of_range")

    # totals should not be negative
    for field_name in ["net_total", "tax_amount", "gross_total"]:
        val = getattr(inv, field_name, None)
        if val is not None and val < 0:
            errors.append(f"business_rule_failed: {field_name}_negative")

    # net_total + tax_amount ≈ gross_total
    if inv.net_total is not None and inv.tax_amount is not None and inv.gross_total is not None:
        if not approx_equal(inv.net_total + inv.tax_amount, inv.gross_total):
            errors.append("business_rule_failed: totals_mismatch")

    # sum of line_items ≈ net_total
    if inv.line_items and inv.net_total is not None:
        sum_lines = sum(li.line_total or 0.0 for li in inv.line_items)
        if not approx_equal(sum_lines, inv.net_total):
            errors.append("business_rule_failed: line_items_sum_mismatch")

    # due_date >= invoice_date
    if inv_date_obj and due_date_obj:
        if due_date_obj < inv_date_obj:
            errors.append("business_rule_failed: due_before_invoice_date")

    # key = (invoice_number, seller_name, invoice_date)
    if inv.invoice_number and inv.seller_name and inv.invoice_date:
        key = (inv.invoice_number, inv.seller_name, inv.invoice_date)
        seen_keys[key] = seen_keys.get(key, 0) + 1
        if seen_keys[key] > 1:
            errors.append("anomaly: duplicate_invoice")

    invoice_id = inv.invoice_number or inv.source_pdf or "<unknown>"

    return InvoiceValidationResult(
        invoice_id=invoice_id,
        is_valid=len(errors) == 0,
        errors=errors,
    )


def validate_invoices(invoices: List[Invoice]) -> ValidationSummary:
    seen_keys: Dict[Tuple[str, str, str], int] = {}
    results: List[InvoiceValidationResult] = []
    error_counter: Counter[str] = Counter()

    for inv in invoices:
        res = validate_single_invoice(inv, seen_keys)
        results.append(res)
        for e in res.errors:
            error_counter[e] += 1

    total = len(results)
    invalid = sum(1 for r in results if not r.is_valid)
    valid = total - invalid

    return ValidationSummary(
        total_invoices=total,
        valid_invoices=valid,
        invalid_invoices=invalid,
        error_counts=dict(error_counter),
        invoices=results,
    )
