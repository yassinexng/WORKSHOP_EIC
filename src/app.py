import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from src.config import config
from src.ingest import ingest_directory
from src.embed import run_embedding
from src.rag import RAGService, REFUSAL_MESSAGE

app = Flask(__name__)
rag_service_instance: RAGService | None = None

def get_rag_service() -> RAGService:
    global rag_service_instance
    if rag_service_instance is None:
        rag_service_instance = RAGService()
    return rag_service_instance

def reload_rag_service() -> RAGService:
    global rag_service_instance
    rag_service_instance = RAGService()
    return rag_service_instance

@app.route("/")
def serve_index():
    return send_from_directory(config.interface_dir, "index.html")

@app.route("/style.css")
def serve_style():
    return send_from_directory(config.interface_dir, "style.css")

@app.route("/app.js")
def serve_script():
    return send_from_directory(config.interface_dir, "app.js")

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route("/api/documents", methods=["GET"])
def list_documents():
    if not config.data_dir.is_dir():
        return jsonify({"documents": []}), 200
    pdf_files = sorted([f.name for f in config.data_dir.glob("*.pdf")])
    return jsonify({"documents": pdf_files}), 200

@app.route("/api/upload", methods=["POST"])
def upload_document():
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier fourni dans la requete."}), 400

    uploaded_file = request.files["file"]
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"error": "Aucun fichier selectionne."}), 400

    filename = secure_filename(uploaded_file.filename)
    if not filename or not filename.lower().endswith(".pdf"):
        return jsonify({"error": "Le fichier doit obligatoirement etre au format PDF (.pdf)."}), 400

    config.data_dir.mkdir(parents=True, exist_ok=True)
    destination = config.data_dir / filename
    uploaded_file.save(str(destination))

    try:
        reader = PdfReader(str(destination))
        if len(reader.pages) == 0:
            destination.unlink(missing_ok=True)
            return jsonify({"error": "Le document PDF ne contient aucune page."}), 400
    except Exception:
        destination.unlink(missing_ok=True)
        return jsonify({"error": "Le fichier PDF fourni est invalide ou endommage."}), 400

    try:
        ingest_directory(config.data_dir, config.chunks_file, config.chunk_size, config.chunk_overlap)
        run_embedding()
        reload_rag_service()
        docs = sorted([f.name for f in config.data_dir.glob("*.pdf")])
        return jsonify({
            "status": "ok",
            "message": f"Le document '{filename}' a ete ajoute et indexe avec succes.",
            "filename": filename,
            "documents": docs
        }), 200
    except Exception:
        return jsonify({"error": "Une erreur est survenue lors du traitement du document PDF."}), 500

@app.route("/api/ask", methods=["POST"])
def ask_question():
    if not request.is_json:
        return jsonify({"error": "Le corps de la requete doit etre un objet JSON contenant la cle 'question'."}), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "question" not in data:
        return jsonify({"error": "Le corps de la requete doit etre un objet JSON contenant la cle 'question'."}), 400

    question = data.get("question")
    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "La question ne peut pas etre vide."}), 400

    try:
        service = get_rag_service()
        response = service.answer_question(question)
        return jsonify(response), 200
    except Exception:
        return jsonify({"error": "Une erreur interne est survenue lors du traitement de votre demande."}), 500

@app.route("/api/documents/<path:filename>", methods=["DELETE"])
def delete_document(filename: str):
    safe_name = secure_filename(filename)
    if not safe_name or not safe_name.lower().endswith(".pdf"):
        return jsonify({"error": "Le nom de fichier est invalide ou n'est pas un PDF."}), 400

    target = config.data_dir / safe_name
    if not target.exists():
        return jsonify({"error": f"Le document '{safe_name}' est introuvable."}), 404

    try:
        target.unlink()
    except OSError:
        return jsonify({"error": "Impossible de supprimer le document."}), 500

    try:
        ingest_directory(config.data_dir, config.chunks_file, config.chunk_size, config.chunk_overlap)
        run_embedding()
        reload_rag_service()
    except Exception:
        pass

    docs = sorted([f.name for f in config.data_dir.glob("*.pdf")])
    return jsonify({
        "status": "ok",
        "message": f"Le document '{safe_name}' a ete supprime avec succes.",
        "documents": docs
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Ressource introuvable."}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"error": "Une erreur interne est survenue lors du traitement de votre demande."}), 500

def main() -> None:
    app.run(
        host=config.host,
        port=config.port,
        debug=False
    )

if __name__ == "__main__":
    main()
