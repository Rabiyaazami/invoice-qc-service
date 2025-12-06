# Invoice QC Service –

A realistic **Invoice Extraction & Quality Control (QC) service** that:

✔ Extracts structured data from **PDF invoices**  
✔ Validates with **schema + business rules**  
✔ Provides both **CLI tools** and a **FastAPI HTTP service**

---

## 📌 Features

| Feature | Status |
|---------|--------|
| PDF → JSON extraction (regex + heuristics) 
| Pydantic schema 
| Validation engine (business rules) 
| CLI (Typer) 
| FastAPI endpoints 
| Swagger UI 
| Bonus UI

---

## 🧾 Schema & Field Definitions

### **Invoice Fields**

| Field | Type | Description |
|------|------|-------------|
| `invoice_number` | string | Unique invoice code |
| `invoice_date` | YYYY-MM-DD | Parsed invoice date |
| `due_date` | Date \| null | Optional |
| `seller_name` | string | Issuer company |
| `seller_address` | string \| null | Issuer address |
| `seller_tax_id` | string \| null | Tax ID if available |
| `buyer_name` | string | Customer company |
| `buyer_address` | string \| null | Customer address |
| `buyer_tax_id` | string \| null | Buyer tax if available |
| `currency` | string | EUR/USD/INR/GBP |
| `net_total` | float | Before tax |
| `tax_amount` | float | Tax |
| `gross_total` | float | Net + Tax |
| `line_items` | list | Optional |
| `source_pdf` | string | PDF file name |

---

## 🛡️ Validation Rules

### 🔵 Completeness
| Rule |
|------|
| `invoice_number` must exist |
| `invoice_date` must exist |
| `seller_name` and `buyer_name` must exist |

### 🟣 Format
| Rule |
|------|
| `invoice_date` must be valid and 2000–2100 |
| `currency` ∈ {EUR, USD, INR, GBP} |

### 🟥 Business Constraints
| Rule |
|------|
| `net_total + tax_amount ≈ gross_total` |
| Totals must not be negative |
| If line items exist → sum(items) ≈ net_total |
| `due_date ≥ invoice_date` if present |

### 🟧 Duplicate Rule
| Rule |
|------|
| `invoice_number + seller + date` must not repeat |

---

## 📦 Architecture Overview

```
PDFs → extractor.py → JSON → validator.py → CLI / API → Reports/UI
```

### 📂 Project Structure

```
invoice-qc-service/
│
├─ invoice_qc/
│   ├─ extractor.py       # PDF → JSON
│   ├─ validator.py       # Validation Core
│   ├─ cli.py             # Typer CLI
│   ├─ schema.py          # Pydantic models
│   └─ api/
│       └─ main.py        # FastAPI app
│
├─ pdfs/                  # Sample invoices
├─ output/                # Extracted & validated JSON
├─ requirements.txt
└─ README.md
```

---

## 🚀 Setup Instructions

```bash
# Clone repo:
git clone https://github.com/<your-github>/invoice-qc-service-
cd invoice-qc-service

# Create venv
python -m venv venv
source venv/bin/activate  

# Install deps
pip install -r requirements.txt
```

---

## 🧰 CLI Usage

### ▶ Extract PDFs

```bash
python -m invoice_qc.cli extract \
  --pdf-dir pdfs \
  --output output/extracted_invoices.json
```

### 🧪 Validate JSON

```bash
python -m invoice_qc.cli validate \
  --input output/extracted_invoices.json \
  --report output/validation_report.json
```

### 🔁 Full Run

```bash
python -m invoice_qc.cli full-run \
  --pdf-dir pdfs \
  --report output/validation_report.json
```

---

## 🌐 FastAPI Service

### ▶ Start Server

```bash
uvicorn invoice_qc.api.main:app --reload
```

### 🧭 Swagger Docs

```
http://127.0.0.1:8000/docs
```

### 📍 Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/health` | Health check |
| POST | `/validate-json` | Validate invoice JSON |

---

### 🧠 Example `POST /validate-json` Request Body

```json
[
  {
    "invoice_number": "AUFNR34343",
    "invoice_date": "2024-05-22",
    "seller_name": "ABC Corporation",
    "buyer_name": "Beispielname Unternehmen",
    "currency": "EUR",
    "net_total": 64.0,
    "tax_amount": 12.16,
    "gross_total": 76.16
  }
]
```

---
## UI -

python -m http.server 8080
http://127.0.0.1:8080/index.html

## 🤖 AI Usage Notes

**Tools used:** ChatGPT  
**Used for:** Regex suggestions, German formatting, README formatting  
**Incorrect Suggestion Fixed:** Initial numeric parsing treated commas wrongly (`1.285,20 → 1.08`). Fixed with European format detection.

---

## 📌 Assumptions & Limitations

- Some invoices lack tax IDs (skipped)
- Line items extraction simplified (can be extended)
- Works only on **text-based PDFs**, not scanned OCR
- Duplicates detected via `(number, seller, date)`

---

## 🎥 Demo Video

🔗 Project and code explanation :- https://www.loom.com/share/59e46fdbdb83479ebd4c5b67f346a5d0
🔗 UI Demo :- https://www.loom.com/share/ccae77c626e049e4b0103dfdf1ebce63



