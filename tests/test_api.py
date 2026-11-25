import io
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from src.app import app
import src.app as app_module
from src.config import config
from src.rag import RAGService
from scripts.generate_sample_pdfs import build_pdf

class MockRAGService:
    def answer_question(self, question: str) -> dict:
        return {
            "answer": "Reponse issue du cours.\n\n[Source : cours_python.pdf, page 1]",
            "sources": [
                {
                    "source": "cours_python.pdf",
                    "page": 1,
                    "chunk_index": 0,
                    "text": "Extrait de cours de test",
                    "distance": 0.12
                }
            ],
            "question": question
        }

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app_module.rag_service_instance = MockRAGService()
    with app.test_client() as test_client:
        yield test_client

def test_frontend_files_exist() -> None:
    index_file = config.interface_dir / "index.html"
    style_file = config.interface_dir / "style.css"
    app_file = config.interface_dir / "app.js"
    assert index_file.is_file()
    assert style_file.is_file()
    assert app_file.is_file()

def test_static_routes(client) -> None:
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "Mon Assistant de Cours" in res_index.get_data(as_text=True)

    res_css = client.get("/style.css")
    assert res_css.status_code == 200
    assert "--primary-blue" in res_css.get_data(as_text=True)

    res_js = client.get("/app.js")
    assert res_js.status_code == 200
    assert "fetchDocuments" in res_js.get_data(as_text=True)

def test_health_endpoint(client) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {"status": "ok"}

def test_documents_endpoint(client) -> None:
    response = client.get("/api/documents")
    assert response.status_code == 200
    data = response.get_json()
    assert "documents" in data
    assert isinstance(data["documents"], list)

def test_ask_rejects_non_json(client) -> None:
    response = client.post(
        "/api/ask",
        data="texte brut non json",
        content_type="text/plain"
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_ask_rejects_missing_question(client) -> None:
    response = client.post(
        "/api/ask",
        json={"other_key": "valeur"}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_ask_rejects_empty_question(client) -> None:
    response = client.post(
        "/api/ask",
        json={"question": "   "}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_ask_returns_expected_schema(client) -> None:
    response = client.post(
        "/api/ask",
        json={"question": "Quelle est la complexite de len() ?"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "answer" in data
    assert "sources" in data
    assert "question" in data
    assert isinstance(data["sources"], list)
    assert data["question"] == "Quelle est la complexite de len() ?"
    assert len(data["sources"]) > 0
    source_item = data["sources"][0]
    assert "source" in source_item
    assert "page" in source_item
    assert "text" in source_item
    assert "distance" in source_item

def test_upload_rejects_missing_file(client) -> None:
    response = client.post("/api/upload", data={})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_upload_rejects_non_pdf(client) -> None:
    data = {
        "file": (io.BytesIO(b"ceci n est pas un pdf"), "cours.txt")
    }
    response = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_upload_rejects_corrupted_pdf(client) -> None:
    data = {
        "file": (io.BytesIO(b"faux contenu pdf"), "cours_corrompu.pdf")
    }
    response = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_upload_valid_pdf(client, tmp_path) -> None:
    sample_pdf = tmp_path / "nouveau_cours.pdf"
    pages_data = [
        {"title": "Nouveau Cours", "sections": [("Section A", "Contenu de test pour upload valide.")]},
        {"title": "Deuxieme Page", "sections": [("Section B", "Suite du contenu de test.")]}
    ]
    build_pdf(sample_pdf, pages_data)
    with open(sample_pdf, "rb") as f:
        data = {
            "file": (f, "cours_upload_test.pdf")
        }
        response = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["status"] == "ok"
    assert "cours_upload_test.pdf" in res_data["documents"]
    test_uploaded_file = config.data_dir / "cours_upload_test.pdf"
    if test_uploaded_file.exists():
        test_uploaded_file.unlink()
