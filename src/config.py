import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
DB_DIR = PROJECT_ROOT / "db"
INTERFACE_DIR = PROJECT_ROOT / "interface"
CHUNKS_FILE = ARTIFACTS_DIR / "chunks.jsonl"
COLLECTION_NAME = "course_chunks"

def load_dotenv_file(dotenv_path: Path) -> None:
    if not dotenv_path.is_file():
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                key, val = stripped.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val

load_dotenv_file(PROJECT_ROOT / ".env")

class Config:
    def __init__(self) -> None:
        self.project_root: Path = PROJECT_ROOT
        self.data_dir: Path = DATA_DIR
        self.artifacts_dir: Path = ARTIFACTS_DIR
        self.db_dir: Path = DB_DIR
        self.interface_dir: Path = INTERFACE_DIR
        self.chunks_file: Path = CHUNKS_FILE
        self.collection_name: str = COLLECTION_NAME

        self.embedding_model: str = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.generation_model: str = os.environ.get("GENERATION_MODEL", "google/flan-t5-small")

        try:
            self.chunk_size: int = int(os.environ.get("CHUNK_SIZE", 900))
        except ValueError:
            raise ValueError("CHUNK_SIZE doit etre un entier valide.")

        try:
            self.chunk_overlap: int = int(os.environ.get("CHUNK_OVERLAP", 150))
        except ValueError:
            raise ValueError("CHUNK_OVERLAP doit etre un entier valide.")

        try:
            self.top_k: int = int(os.environ.get("TOP_K", 3))
        except ValueError:
            raise ValueError("TOP_K doit etre un entier valide.")

        try:
            self.distance_threshold: float = float(os.environ.get("DISTANCE_THRESHOLD", 0.55))
        except ValueError:
            raise ValueError("DISTANCE_THRESHOLD doit etre un nombre flottant valide.")

        self.host: str = os.environ.get("HOST", "127.0.0.1")

        try:
            self.port: int = int(os.environ.get("PORT", 5000))
        except ValueError:
            raise ValueError("PORT doit etre un entier valide.")

        try:
            self.max_new_tokens: int = int(os.environ.get("MAX_NEW_TOKENS", 128))
        except ValueError:
            raise ValueError("MAX_NEW_TOKENS doit etre un entier valide.")

        self.validate()

    def validate(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("CHUNK_SIZE doit etre strictement positif.")
        if self.chunk_overlap < 0:
            raise ValueError("CHUNK_OVERLAP doit etre positif ou nul.")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP doit etre strictement inferieur a CHUNK_SIZE.")
        if self.top_k <= 0:
            raise ValueError("TOP_K doit etre strictement positif.")
        if not (0.0 <= self.distance_threshold <= 2.0):
            raise ValueError("DISTANCE_THRESHOLD doit etre compris entre 0.0 et 2.0.")
        if not (1 <= self.port <= 65535):
            raise ValueError("PORT doit etre compris entre 1 et 65535.")
        if self.max_new_tokens <= 0:
            raise ValueError("MAX_NEW_TOKENS doit etre strictement positif.")

config = Config()
