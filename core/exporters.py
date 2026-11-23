"""Export the documentation to Markdown and Word (spec FR-9)."""

from __future__ import annotations

import io
import re

from docx import Document

from core.schemas import DocumentationOutput

DRAFT_NOTE = "AI-generated draft – review required."


def safe_filename(rule_name: str, extension: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", rule_name).strip("_") or "rule"
    return f"{stem}_documentation.{extension}"


def _sections(doc: DocumentationOutput) -> list[tuple[str, list[str], list[list[str]]]]:
    """Return (heading, header_row, rows) for each table section."""
    return [
        ("POV / FIX scope", ["Dimension", "Members", "Lines"],
         [[s.dimension, s.members, s.source_lines] for s in doc.pov_fix_scope]),
        ("Dimensions and members", ["Dimension", "Read", "Written"],
         [[d.dimension, d.members_read, d.members_written] for d in doc.dimensions_and_members]),
        ("Run-time prompts", ["Name", "Purpose"],
         [[r.name, r.purpose] for r in doc.runtime_prompts]),
        ("Step-by-step logic", ["Step", "Description", "Lines"],
         [[str(s.step), s.description, s.source_lines] for s in doc.logic_steps]),
        ("Risks and performance notes", ["Severity", "Note"],
         [[r.severity, r.note] for r in doc.risks_and_performance_notes]),
    ]


def _md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def to_markdown(doc: DocumentationOutput) -> str:
    out = [
        f"# {doc.rule_name}",
        "",
        f"**Rule type:** {doc.rule_type} · **AI confidence:** {doc.confidence}",
        "",
        "## Purpose",
        "",
        doc.purpose,
        "",
    ]
    for heading, header, rows in _sections(doc):
        out += [f"## {heading}", ""]
        if not rows:
            out += ["None found.", ""]
            continue
        out.append("| " + " | ".join(header) + " |")
        out.append("|" + "---|" * len(header))
        out += ["| " + " | ".join(_md_cell(c) for c in row) + " |" for row in rows]
        out.append("")
    out += ["---", f"*{DRAFT_NOTE}*", ""]
    return "\n".join(out)


def to_docx(doc: DocumentationOutput) -> bytes:
    document = Document()
    document.add_heading(doc.rule_name, level=0)
    document.add_paragraph(f"Rule type: {doc.rule_type}  ·  AI confidence: {doc.confidence}")
    document.add_heading("Purpose", level=1)
    document.add_paragraph(doc.purpose)

    for heading, header, rows in _sections(doc):
        document.add_heading(heading, level=1)
        if not rows:
            document.add_paragraph("None found.")
            continue
        table = document.add_table(rows=1, cols=len(header))
        table.style = "Light Grid Accent 1"
        for cell, text in zip(table.rows[0].cells, header):
            cell.text = text
        for row in rows:
            cells = table.add_row().cells
            for cell, text in zip(cells, row):
                cell.text = text

    footer = document.add_paragraph(DRAFT_NOTE)
    footer.runs[0].italic = True

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()
