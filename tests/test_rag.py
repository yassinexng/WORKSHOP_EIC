import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Any
from src.rag import RAGService, REFUSAL_MESSAGE

class FakeEmbeddingService:
    def __init__(self, model_name: str = "fake-embed") -> None:
        self.model_name = model_name

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

class FakeLLMService:
    def __init__(self, answer: str = "Reponse factuelle de test.") -> None:
        self.answer = answer
        self.last_prompt = ""

    def generate_answer(self, prompt: str, max_new_tokens: int = 128) -> str:
        self.last_prompt = prompt
        return self.answer

class FakeCollection:
    def __init__(self, results: dict[str, list]) -> None:
        self.results = results

    def query(self, query_embeddings: list[list[float]], n_results: int, include: list[str]) -> dict[str, list]:
        return self.results

def test_empty_question_rejected() -> None:
    service = RAGService(
        embedding_service=FakeEmbeddingService(),
        llm_service=FakeLLMService()
    )
    result = service.answer_question("")
    assert result["answer"] == REFUSAL_MESSAGE
    assert result["sources"] == []

    result_spaces = service.answer_question("   \t  \n ")
    assert result_spaces["answer"] == REFUSAL_MESSAGE
    assert result_spaces["sources"] == []

def test_out_of_context_question_produces_refusal() -> None:
    fake_coll = FakeCollection({
        "documents": [["Texte sans rapport."]],
        "metadatas": [[{"source": "cours_sql.pdf", "page": 1, "chunk_index": 0}]],
        "distances": [[0.95]]
    })
    service = RAGService(
        embedding_service=FakeEmbeddingService(),
        llm_service=FakeLLMService("Reponse quelconque"),
        distance_threshold=0.7
    )
    service._collection = fake_coll
    result = service.answer_question("Quelle est la vitesse de la lumiere ?")
    assert result["answer"] == REFUSAL_MESSAGE
    assert result["sources"] == []

def test_model_unfound_produces_refusal() -> None:
    fake_coll = FakeCollection({
        "documents": [["Texte partiel."]],
        "metadatas": [[{"source": "cours_python.pdf", "page": 2, "chunk_index": 0}]],
        "distances": [[0.3]]
    })
    service = RAGService(
        embedding_service=FakeEmbeddingService(),
        llm_service=FakeLLMService("Information introuvable dans le document"),
        distance_threshold=0.7
    )
    service._collection = fake_coll
    result = service.answer_question("Question sans reponse dans le contexte")
    assert result["answer"] == REFUSAL_MESSAGE
    assert result["sources"] == []

def test_successful_answer_with_sources_metadata() -> None:
    fake_coll = FakeCollection({
        "documents": [
            ["La fonction len() est O(1)."],
            ["La fonction len() est en temps constant."]
        ],
        "metadatas": [
            [
                {"source": "cours_python.pdf", "page": 1, "chunk_index": 0},
                {"source": "cours_python.pdf", "page": 1, "chunk_index": 1}
            ]
        ],
        "distances": [[0.15, 0.18]]
    })
    service = RAGService(
        embedding_service=FakeEmbeddingService(),
        llm_service=FakeLLMService("La fonction len() s execute en O(1)."),
        distance_threshold=0.7
    )
    service._collection = fake_coll
    result = service.answer_question("Quelle est la complexite de len() en Python ?")
    assert "La fonction len() s execute en O(1)." in result["answer"]
    assert "[Source : cours_python.pdf, page 1]" in result["answer"]
    assert len(result["sources"]) == 1
    assert result["sources"][0]["source"] == "cours_python.pdf"
    assert result["sources"][0]["page"] == 1

def test_deduplicate_sources() -> None:
    service = RAGService(
        embedding_service=FakeEmbeddingService(),
        llm_service=FakeLLMService()
    )
    chunks = [
        {"source": "cours_html_css.pdf", "page": 2, "chunk_index": 0, "text": "A", "distance": 0.1},
        {"source": "cours_html_css.pdf", "page": 2, "chunk_index": 1, "text": "B", "distance": 0.2},
        {"source": "cours_python.pdf", "page": 1, "chunk_index": 0, "text": "C", "distance": 0.3}
    ]
    deduped = service.deduplicate_sources(chunks)
    assert len(deduped) == 2
    sources = [(s["source"], s["page"]) for s in deduped]
    assert sources == [("cours_html_css.pdf", 2), ("cours_python.pdf", 1)]
