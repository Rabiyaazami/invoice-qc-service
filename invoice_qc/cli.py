from __future__ import annotations

import json
from pathlib import Path
import sys

import typer

from .extractor import extract_invoices_from_dir
from .validator import validate_invoices
from .schema import Invoice

app = typer.Typer(help="Invoice QC CLI – extract and validate invoice PDFs")


@app.command("extract")
def extract(
    pdf_dir: str = typer.Option(..., help="Directory containing invoice PDFs"),
    output: str = typer.Option(..., help="Path to write extracted JSON"),
):
    pdf_path = Path(pdf_dir)
    if not pdf_path.exists() or not pdf_path.is_dir():
        typer.echo(f"ERROR: pdf_dir '{pdf_dir}' does not exist or is not a directory.")
        raise typer.Exit(code=1)

    invoices = extract_invoices_from_dir(pdf_path)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = [inv.model_dump() for inv in invoices]

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    typer.echo(f"Extracted {len(invoices)} invoices to {output_path}")


@app.command("validate")
def validate(
    input: str = typer.Option(..., help="JSON file with extracted invoices"),
    report: str = typer.Option(..., help="Path to write validation report JSON"),
):
    input_path = Path(input)
    if not input_path.exists():
        typer.echo(f"ERROR: input file '{input}' does not exist.")
        raise typer.Exit(code=1)

    with input_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    invoices = [Invoice(**item) for item in raw]
    summary = validate_invoices(invoices)

    report_path = Path(report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(summary.model_dump(), f, indent=2, ensure_ascii=False)


    typer.echo(
        f"Validated {summary.total_invoices} invoices: "
        f"{summary.valid_invoices} valid, {summary.invalid_invoices} invalid."
    )
    typer.echo(f"Report written to {report_path}")

    if summary.invalid_invoices > 0:
        typer.echo("Some invoices are invalid.", err=True)
        raise typer.Exit(code=2)


@app.command("full-run")
def full_run(
    pdf_dir: str = typer.Option(..., help="Directory containing invoice PDFs"),
    report: str = typer.Option(..., help="Path to write validation report JSON"),
):
    pdf_path = Path(pdf_dir)
    if not pdf_path.exists() or not pdf_path.is_dir():
        typer.echo(f"ERROR: pdf_dir '{pdf_dir}' does not exist or is not a directory.")
        raise typer.Exit(code=1)

    invoices = extract_invoices_from_dir(pdf_path)
    summary = validate_invoices(invoices)

    report_path = Path(report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(summary.model_dump(), f, indent=2, ensure_ascii=False)


    typer.echo(
        f"[FULL-RUN] {summary.total_invoices} invoices: "
        f"{summary.valid_invoices} valid, {summary.invalid_invoices} invalid."
    )
    typer.echo(f"Report written to {report_path}")

    if summary.invalid_invoices > 0:
        raise typer.Exit(code=2)


def main():
    app()


if __name__ == "__main__":
    main()
