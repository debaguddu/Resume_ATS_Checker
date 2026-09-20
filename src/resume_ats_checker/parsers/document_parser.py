"""Unified multi-format document parser for PDF, DOCX, PPTX, and TXT files."""

import io
import re
from typing import Dict, Any, Tuple
from pypdf import PdfReader
from docx import Document as DocxDocument
from pptx import Presentation


def clean_text(text: str) -> str:
    """Normalize whitespace and remove non-printable characters while preserving paragraph breaks."""
    if not text:
        return ""
    # Normalize unicode carriage returns and excessive tabs
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse multiple blank lines into max 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip trailing and leading whitespace
    return text.strip()


def parse_pdf(file_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
    """Extract text and metadata from a PDF file."""
    reader = PdfReader(io.BytesIO(file_bytes))
    num_pages = len(reader.pages)
    text_chunks = []

    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        if page_text.strip():
            text_chunks.append(f"--- Page {i + 1} ---\n{page_text.strip()}")

    full_text = clean_text("\n\n".join(text_chunks))
    metadata = {
        "format": "pdf",
        "page_count": num_pages,
        "char_count": len(full_text),
    }
    return full_text, metadata


def parse_docx(file_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
    """Extract text from Word document (DOCX), including paragraphs and tables."""
    doc = DocxDocument(io.BytesIO(file_bytes))
    text_chunks = []

    # Extract paragraphs
    for p in doc.paragraphs:
        if p.text.strip():
            text_chunks.append(p.text.strip())

    # Extract tables (useful for skills and education layouts)
    for table in doc.tables:
        table_rows = []
        for row in table.rows:
            row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_cells:
                # Deduplicate repeated merged cell values in row
                deduped = []
                for cell_val in row_cells:
                    if not deduped or deduped[-1] != cell_val:
                        deduped.append(cell_val)
                table_rows.append(" | ".join(deduped))
        if table_rows:
            text_chunks.append("\n".join(table_rows))

    full_text = clean_text("\n\n".join(text_chunks))
    metadata = {
        "format": "docx",
        "paragraph_count": len(doc.paragraphs),
        "table_count": len(doc.tables),
        "char_count": len(full_text),
    }
    return full_text, metadata


def parse_pptx(file_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
    """Extract text from PowerPoint presentations (PPTX), including shapes, text boxes, and notes."""
    prs = Presentation(io.BytesIO(file_bytes))
    num_slides = len(prs.slides)
    text_chunks = []

    for idx, slide in enumerate(prs.slides):
        slide_texts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    line = "".join(run.text for run in paragraph.runs).strip()
                    if line:
                        slide_texts.append(line)
            elif shape.has_table:
                for row in shape.table.rows:
                    row_vals = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_vals:
                        slide_texts.append(" | ".join(row_vals))

        # Check speaker notes if present
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                slide_texts.append(f"[Speaker Notes: {notes}]")

        if slide_texts:
            text_chunks.append(f"--- Slide {idx + 1} ---\n" + "\n".join(slide_texts))

    full_text = clean_text("\n\n".join(text_chunks))
    metadata = {
        "format": "pptx",
        "slide_count": num_slides,
        "char_count": len(full_text),
    }
    return full_text, metadata


def parse_document(file_name: str, file_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
    """Universal document parsing entrypoint based on file extension.
    
    Supports: .pdf, .docx, .pptx, .txt, .md
    Provides clear error handling and guidance for legacy formats (.doc, .ppt).
    """
    ext = file_name.lower().split(".")[-1]

    if ext == "pdf":
        return parse_pdf(file_bytes)
    elif ext == "docx":
        return parse_docx(file_bytes)
    elif ext == "pptx":
        return parse_pptx(file_bytes)
    elif ext in ("txt", "md"):
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1", errors="ignore")
        cleaned = clean_text(text)
        return cleaned, {"format": ext, "char_count": len(cleaned)}
    elif ext == "doc":
        # Legacy binary Word document
        # Attempt to read printable strings with guidance
        printable = re.findall(rb"[\x20-\x7E]{4,}", file_bytes)
        extracted = "\n".join(chunk.decode("ascii", errors="ignore") for chunk in printable)
        cleaned = clean_text(extracted)
        if len(cleaned) > 200:
            return cleaned, {"format": "doc", "char_count": len(cleaned), "warning": "Extracted text from legacy binary .doc file. For best accuracy, save as .docx or .pdf."}
        raise ValueError("Legacy .doc format detected. Please save or convert your document to .docx or .pdf for accurate ATS text parsing.")
    elif ext == "ppt":
        printable = re.findall(rb"[\x20-\x7E]{4,}", file_bytes)
        extracted = "\n".join(chunk.decode("ascii", errors="ignore") for chunk in printable)
        cleaned = clean_text(extracted)
        if len(cleaned) > 200:
            return cleaned, {"format": "ppt", "char_count": len(cleaned), "warning": "Extracted text from legacy binary .ppt file. For best accuracy, save as .pptx or .pdf."}
        raise ValueError("Legacy .ppt format detected. Please save or convert your presentation to .pptx or .pdf for accurate ATS text parsing.")
    else:
        raise ValueError(f"Unsupported file format: .{ext}. Supported formats: PDF, DOCX, PPTX, TXT.")
