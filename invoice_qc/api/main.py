from __future__ import annotations

from typing import List
from pathlib import Path
import tempfile

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from ..schema import Invoice, ValidationSummary
from ..validator import validate_invoices
from ..extractor import extract_invoice_from_pdf

app = FastAPI(
    title="Invoice QC Service",
    description="Extract + Validate invoices via API",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/validate-json", response_model=ValidationSummary)
def validate_json(invoices: List[Invoice]):

    """
    Accepts a list of invoice JSON objects and returns
    per-invoice validation + summary.
    """
    summary = validate_invoices(invoices)
    return summary

# ---------------------------------------------------------
# 📎 BONUS: Upload PDFs → Extract + Validate
# ---------------------------------------------------------
@app.post("/extract-and-validate-pdfs", response_model=ValidationSummary)
async def extract_and_validate_pdfs(pdfs: List[UploadFile] = File(...)):
    """
    Upload PDF files → Extract invoices → Validate → Return summary.
    Ideal for UI uploads.
    """
    invoices: List[Invoice] = []

    for pdf in pdfs:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await pdf.read())
            tmp_path = Path(tmp.name)

        # Extract structured invoice data
        invoices.append(extract_invoice_from_pdf(tmp_path))

    summary = validate_invoices(invoices)
    return summary
