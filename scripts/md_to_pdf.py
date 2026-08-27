"""Convert the Markdown knowledge base into PDF documents.

Run once (or whenever the Markdown sources change) to (re)generate the PDFs the
RAG pipeline indexes:

    python scripts/md_to_pdf.py
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

KB_DIR = Path(__file__).resolve().parent.parent / "data" / "banking_kb"


def _markdown_to_flowables(text: str, styles) -> list:
    flowables = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            flowables.append(Spacer(1, 6))
            continue
        if line.startswith("# "):
            flowables.append(Paragraph(line[2:], styles["Title"]))
        elif line.startswith("## "):
            flowables.append(Paragraph(line[3:], styles["Heading2"]))
        elif line.startswith("### "):
            flowables.append(Paragraph(line[4:], styles["Heading3"]))
        elif line.startswith(("- ", "* ")):
            flowables.append(Paragraph(line[2:], styles["Bullet"]))
        else:
            flowables.append(Paragraph(line, styles["BodyText"]))
    return flowables


def convert(path: Path, styles) -> Path:
    pdf_path = path.with_suffix(".pdf")
    doc = SimpleDocTemplate(str(pdf_path), pagesize=LETTER)
    doc.build(_markdown_to_flowables(path.read_text(encoding="utf-8"), styles))
    return pdf_path


def main() -> None:
    styles = getSampleStyleSheet()
    for md in sorted(KB_DIR.glob("*.md")):
        out = convert(md, styles)
        print(f"{md.name} -> {out.name}")


if __name__ == "__main__":
    main()
