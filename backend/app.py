# backend/app.py
"""
Flask backend for MedExplain AI.
Serves the frontend and exposes REST API endpoints.

Endpoints:
    GET  /health          — liveness check for Render wakeup
    POST /api/analyze     — upload PDF + get full analysis
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from pdf_parser import PDFParser
from report_analyzer import ReportAnalyzer

load_dotenv()

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend", "static"),
    template_folder=os.path.join(os.path.dirname(__file__), "..", "frontend", "templates"),
)
CORS(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MAX_FILE_SIZE_MB = 10
ALLOWED_LANGUAGES = ["English", "Hungarian", "German", "French", "Spanish", "Arabic", "Turkish"]


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), "..", "frontend", "templates"),
        "index.html"
    )

@app.route("/health")
def health():
    """Liveness check — used by wakeup screen to detect when server is ready."""
    return jsonify({"status": "ok", "model": ReportAnalyzer.MODEL})


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Accepts a multipart form upload with:
        file     — PDF file (required)
        language — response language (optional, default English)

    Returns JSON with full structured analysis.
    """
    # ── Validate request ───────────────────────────────────────────────────────
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Please attach a PDF."}), 400

    file = request.files["file"]
    language = request.form.get("language", "English")

    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported."}), 400

    if language not in ALLOWED_LANGUAGES:
        language = "English"

    # ── Read and size-check file ───────────────────────────────────────────────
    pdf_bytes = file.read()
    size_mb = len(pdf_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return jsonify({"error": f"File too large ({size_mb:.1f} MB). Maximum is {MAX_FILE_SIZE_MB} MB."}), 400

    # ── Parse PDF ─────────────────────────────────────────────────────────────
    try:
        parser = PDFParser(pdf_bytes)
        parsed = parser.parse()
    except Exception as e:
        return jsonify({"error": f"Could not read PDF: {str(e)}"}), 422

    if parsed["is_scanned"]:
        return jsonify({
            "error": "This PDF appears to be a scanned image with no readable text. "
                     "Please upload a text-based PDF or type your results manually."
        }), 422

    if parsed["word_count"] < 20:
        return jsonify({
            "error": "Very little text found in this PDF. "
                     "It may be encrypted, corrupted, or image-only."
        }), 422

    # ── Analyze with LLM ──────────────────────────────────────────────────────
    if not GROQ_API_KEY:
        return jsonify({"error": "Server is not configured with an AI API key."}), 503

    try:
        analyzer = ReportAnalyzer(GROQ_API_KEY)
        analysis = analyzer.analyze(parsed["text"], language=language)
    except ValueError as e:
        return jsonify({"error": f"AI analysis failed: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Unexpected error during analysis: {str(e)}"}), 500

    # ── Return enriched response ───────────────────────────────────────────────
    return jsonify({
        "success": True,
        "meta": {
            "pages": parsed["pages"],
            "word_count": parsed["word_count"],
            "language": language,
            "filename": file.filename,
        },
        "analysis": analysis,
    })


# ── Dev server ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
