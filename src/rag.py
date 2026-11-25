import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import chromadb
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from src.config import config
from src.embed import EmbeddingService, get_chroma_client, get_or_create_collection

REFUSAL_MESSAGE = "Je ne trouve pas cette information dans les documents fournis."

class LLMService:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or config.generation_model
        self._tokenizer: AutoTokenizer | None = None
        self._model: AutoModelForSeq2SeqLM | None = None

    def load(self) -> tuple[AutoTokenizer, AutoModelForSeq2SeqLM]:
        if self._tokenizer is None or self._model is None:
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        return self._tokenizer, self._model

    def generate_answer(self, prompt: str, max_new_tokens: int = 128) -> str:
        tokenizer, model = self.load()
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=1.0
        )
        answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return answer.strip()

class RAGService:
    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        llm_service: LLMService | None = None,
        db_path: Path = config.db_dir,
        collection_name: str = config.collection_name,
        top_k: int = config.top_k,
        distance_threshold: float = config.distance_threshold,
        max_new_tokens: int = config.max_new_tokens
    ) -> None:
        self.embedding_service = embedding_service or EmbeddingService(config.embedding_model)
        self.llm_service = llm_service or LLMService(config.generation_model)
        self.db_path = db_path
        self.collection_name = collection_name
        self.top_k = top_k
        self.distance_threshold = distance_threshold
        self.max_new_tokens = max_new_tokens
        self._collection = None

    def get_collection(self):
        if self._collection is None:
            client = get_chroma_client(self.db_path)
            self._collection = get_or_create_collection(client, self.collection_name)
        return self._collection

    def retrieve_relevant_chunks(self, question: str) -> list[dict[str, Any]]:
        collection = self.get_collection()
        query_embedding = self.embedding_service.encode([question])[0]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=self.top_k,
            include=["documents", "metadatas", "distances"]
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        filtered_chunks = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            if dist <= self.distance_threshold:
                filtered_chunks.append({
                    "text": doc,
                    "source": meta.get("source", "inconnu"),
                    "page": meta.get("page", 1),
                    "chunk_index": meta.get("chunk_index", 0),
                    "distance": float(dist)
                })
        return filtered_chunks

    def deduplicate_sources(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        deduped = []
        for chunk in chunks:
            key = (chunk["source"], chunk["page"])
            if key not in seen:
                seen.add(key)
                deduped.append(chunk)
        return deduped

    def build_prompt(self, context_chunks: list[dict[str, Any]], question: str) -> str:
        passages = " ".join(chunk["text"] for chunk in context_chunks)
        return (
            f"Contexte: {passages}\n\n"
            "Instruction: Reponds a la question en te basant uniquement sur le contexte ci-dessus. N'invente aucun fait.\n"
            f"Question: {question}\n\n"
            "Reponse:"
        )

    def answer_question(self, question: str) -> dict[str, Any]:
        normalized_question = question.strip()
        if not normalized_question:
            return {
                "answer": REFUSAL_MESSAGE,
                "sources": [],
                "question": question
            }

        retrieved_chunks = self.retrieve_relevant_chunks(normalized_question)
        if not retrieved_chunks:
            return {
                "answer": REFUSAL_MESSAGE,
                "sources": [],
                "question": normalized_question
            }

        deduped_sources = self.deduplicate_sources(retrieved_chunks)
        prompt = self.build_prompt(retrieved_chunks, normalized_question)
        raw_answer = self.llm_service.generate_answer(prompt, max_new_tokens=self.max_new_tokens)

        lower_answer = raw_answer.lower()
        if "information introuvable" in lower_answer or not raw_answer.strip():
            return {
                "answer": REFUSAL_MESSAGE,
                "sources": [],
                "question": normalized_question
            }

        citation_tokens = [f"[Source : {s['source']}, page {s['page']}]" for s in deduped_sources]
        citations_string = " ".join(dict.fromkeys(citation_tokens))
        final_answer = f"{raw_answer.strip()}\n\n{citations_string}"

        structured_sources = [
            {
                "source": s["source"],
                "page": s["page"],
                "chunk_index": s["chunk_index"],
                "text": s["text"],
                "distance": round(s["distance"], 4)
            }
            for s in deduped_sources
        ]

        return {
            "answer": final_answer,
            "sources": structured_sources,
            "question": normalized_question
        }

def run_interactive_cli() -> None:
    print("Initialisation du service RAG...")
    try:
        service = RAGService()
    except Exception as e:
        print(f"Erreur d'initialisation : {e}", file=sys.stderr)
        return

    print("Bienvenue dans le terminal de l'Assistant de cours.")
    print("Posez vos questions ou tapez 'quitter' pour arreter.")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nVotre question : ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nArret du service RAG.")
            break

        if not user_input:
            continue
        if user_input.lower() == "quitter":
            print("Au revoir.")
            break

        result = service.answer_question(user_input)
        print("\nReponse :")
        print(result["answer"])
        if result["sources"]:
            print("\nSources consultees :")
            for s in result["sources"]:
                print(f" - {s['source']} (page {s['page']}, distance: {s['distance']})")

def main() -> None:
    run_interactive_cli()

if __name__ == "__main__":
    main()
