import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pypdf import PdfReader
from src.config import config

def clean_text(text: str) -> str:
    cleaned = re.sub(r'[\r\n\t]+', ' ', text)
    cleaned = re.sub(r' +', ' ', cleaned)
    return cleaned.strip()

def split_text_into_chunks(text: str, chunk_size: int = 900, chunk_overlap: int = 150) -> list[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]
    step = chunk_size - chunk_overlap
    if step <= 0:
        step = chunk_size
    chunks = []
    start = 0
    total_len = len(cleaned)
    while start < total_len:
        end = start + chunk_size
        chunk = cleaned[start:end]
        chunks.append(chunk)
        if end >= total_len:
            break
        start += step
    return chunks

def extract_chunks_from_pdf(pdf_path: Path, chunk_size: int = 900, chunk_overlap: int = 150) -> tuple[list[dict[str, Any]], int]:
    reader = PdfReader(str(pdf_path))
    chunks = []
    page_count = len(reader.pages)
    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        raw_text = page.extract_text() or ""
        cleaned = clean_text(raw_text)
        if not cleaned:
            print(f"Avertissement : La page {page_num} du fichier {pdf_path.name} ne contient aucun texte extractible.", file=sys.stderr)
            continue
        page_chunks = split_text_into_chunks(cleaned, chunk_size, chunk_overlap)
        stem = pdf_path.stem
        for c_idx, chunk_text in enumerate(page_chunks):
            chunk_id = f"{stem}_p{page_num}_c{c_idx}"
            chunks.append({
                "id": chunk_id,
                "source": pdf_path.name,
                "page": page_num,
                "chunk_index": c_idx,
                "text": chunk_text
            })
    return chunks, page_count

def ingest_directory(data_dir: Path, output_file: Path, chunk_size: int = 900, chunk_overlap: int = 150) -> tuple[int, int, int]:
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Le dossier source {data_dir} n'existe pas.")
    pdf_files = sorted(list(data_dir.glob("*.pdf")))
    if not pdf_files:
        raise FileNotFoundError(f"Aucun fichier PDF trouve dans le dossier {data_dir}.")
    all_chunks = []
    total_pages = 0
    for pdf in pdf_files:
        file_chunks, pages = extract_chunks_from_pdf(pdf, chunk_size, chunk_overlap)
        all_chunks.extend(file_chunks)
        total_pages += pages
    output_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = output_file.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    temp_file.replace(output_file)
    return len(pdf_files), total_pages, len(all_chunks)

def main() -> None:
    try:
        pdf_count, page_count, chunk_count = ingest_directory(
            config.data_dir,
            config.chunks_file,
            config.chunk_size,
            config.chunk_overlap
        )
        print(f"Ingestion terminee : {pdf_count} document(s) PDF traites, {page_count} page(s) extraites, {chunk_count} fragment(s) generes.")
    except Exception as e:
        print(f"Erreur lors de l'ingestion : {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
