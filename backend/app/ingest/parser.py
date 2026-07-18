"""Document parsers for supported upload formats.

MEMORY.md checklist:
- [ ] Multi-format upload + parsers (PDF, DOCX, PPTX, TXT, CSV)

Each parser turns raw bytes into plain text (plus optional metadata) ready for
chunking. Real extraction libraries are declared in requirements.txt.
"""

from __future__ import annotations


def parse_pdf(data: bytes) -> str:
    # TODO: extract text with pypdf.
    raise NotImplementedError


def parse_docx(data: bytes) -> str:
    # TODO: extract text with python-docx.
    raise NotImplementedError


def parse_pptx(data: bytes) -> str:
    # TODO: extract text from slides with python-pptx.
    raise NotImplementedError


def parse_txt(data: bytes) -> str:
    # TODO: decode text with correct encoding detection.
    raise NotImplementedError


def parse_csv(data: bytes) -> str:
    # TODO: parse rows and flatten to text for indexing.
    raise NotImplementedError


# Dispatch table by file extension. See documents.upload_document().
PARSERS = {
    "pdf": parse_pdf,
    "docx": parse_docx,
    "pptx": parse_pptx,
    "txt": parse_txt,
    "csv": parse_csv,
}


def parse(filename: str, data: bytes) -> str:
    """Route a file to the correct parser based on its extension."""
    ext = filename.rsplit(".", 1)[-1].lower()
    parser = PARSERS.get(ext)
    if parser is None:
        raise ValueError(f"Unsupported format: {ext}")
    return parser(data)
