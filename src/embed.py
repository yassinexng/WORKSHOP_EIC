import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from sentence_transformers import SentenceTransformer
from src.config import config

class EmbeddingService:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or config.embedding_model
        self._model: SentenceTransformer | None = None

    def get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: list[str]) -> list[list[float]]:
        model = self.get_model()
        embeddings = model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

def load_chunks_from_file(chunks_path: Path) -> list[dict[str, Any]]:
    if not chunks_path.is_file():
        raise FileNotFoundError("Le fichier 'artifacts/chunks.jsonl' est introuvable. Veuillez d'abord executer 'python src/ingest.py'.")
    chunks = []
    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                chunks.append(json.loads(stripped))
    return chunks

def get_chroma_client(db_path: Path) -> ClientAPI:
    db_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(db_path))

def get_or_create_collection(client: ClientAPI, collection_name: str) -> Collection:
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

def index_chunks(
    chunks: list[dict[str, Any]],
    embedding_service: EmbeddingService | None = None,
    db_path: Path = config.db_dir,
    collection_name: str = config.collection_name
) -> int:
    if not chunks:
        return 0
    if embedding_service is None:
        embedding_service = EmbeddingService(config.embedding_model)

    client = get_chroma_client(db_path)
    collection = get_or_create_collection(client, collection_name)

    ids = [chunk["id"] for chunk in chunks]
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [
        {
            "source": chunk["source"],
            "page": int(chunk["page"]),
            "chunk_index": int(chunk["chunk_index"])
        }
        for chunk in chunks
    ]

    embeddings = embedding_service.encode(texts)

    collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
        embeddings=embeddings
    )

    existing_data = collection.get()
    existing_ids = set(existing_data.get("ids", []))
    current_ids = set(ids)
    stale_ids = list(existing_ids - current_ids)
    if stale_ids:
        collection.delete(ids=stale_ids)

    return len(chunks)

def run_embedding() -> int:
    chunks = load_chunks_from_file(config.chunks_file)
    indexed_count = index_chunks(
        chunks=chunks,
        db_path=config.db_dir,
        collection_name=config.collection_name
    )
    print(f"Indexation terminee avec succes : {indexed_count} fragment(s) indexes dans la collection '{config.collection_name}'.")
    return indexed_count

def main() -> None:
    try:
        run_embedding()
    except Exception as e:
        print(f"Erreur lors de l'indexation : {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
