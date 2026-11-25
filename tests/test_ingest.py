import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from src.ingest import clean_text, split_text_into_chunks, extract_chunks_from_pdf, ingest_directory
from scripts.generate_sample_pdfs import build_pdf

def test_clean_text() -> None:
    raw = "  Bonjour   monde \n\n ceci   est\tun   test  "
    cleaned = clean_text(raw)
    assert cleaned == "Bonjour monde ceci est un test"

def test_split_text_into_chunks_single() -> None:
    text = "Phrase courte de test."
    chunks = split_text_into_chunks(text, chunk_size=100, chunk_overlap=20)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_split_text_into_chunks_overlap() -> None:
    text = "0123456789" * 20
    chunk_size = 50
    chunk_overlap = 10
    chunks = split_text_into_chunks(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    assert len(chunks) > 1
    for i in range(len(chunks) - 1):
        overlap_part = chunks[i][-chunk_overlap:]
        assert chunks[i + 1].startswith(overlap_part)

def test_extract_chunks_page_metadata_starts_at_one(tmp_path: Path) -> None:
    pdf_file = tmp_path / "test_doc.pdf"
    pages_data = [
        {"title": "Page 1 Titre", "sections": [("Sec 1", "Contenu de la premiere page.")]},
        {"title": "Page 2 Titre", "sections": [("Sec 2", "Contenu de la deuxieme page.")]}
    ]
    build_pdf(pdf_file, pages_data)
    chunks, page_count = extract_chunks_from_pdf(pdf_file, chunk_size=500, chunk_overlap=50)
    assert page_count == 2
    assert len(chunks) >= 2
    pages = [c["page"] for c in chunks]
    assert min(pages) == 1
    assert 1 in pages
    assert 2 in pages

def test_chunk_identifiers_are_stable(tmp_path: Path) -> None:
    pdf_file = tmp_path / "sample.pdf"
    pages_data = [
        {"title": "Page Titre", "sections": [("S", "Du texte repetable.")]}
    ]
    build_pdf(pdf_file, pages_data)
    chunks_run_1, _ = extract_chunks_from_pdf(pdf_file, chunk_size=300, chunk_overlap=50)
    chunks_run_2, _ = extract_chunks_from_pdf(pdf_file, chunk_size=300, chunk_overlap=50)
    ids_1 = [c["id"] for c in chunks_run_1]
    ids_2 = [c["id"] for c in chunks_run_2]
    assert ids_1 == ids_2
    assert ids_1[0] == "sample_p1_c0"

def test_ingest_directory_empty_raises(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty_data"
    empty_dir.mkdir()
    out_file = tmp_path / "artifacts" / "chunks.jsonl"
    with pytest.raises(FileNotFoundError):
        ingest_directory(empty_dir, out_file)
