# app.py
# Flask app that exposes endpoints to transcribe audio, summarize, create PDF, store on MinIO, and optionally send the PDF by email.
# It uses the services in services/.

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from services.speech_to_text import transcribe_audio
from services.summarizer import generate_summary_and_tasks
from services.pdf_generator import create_meeting_pdf
from services.storage import upload_file, get_presigned_url, AUDIO_BUCKET, PDF_BUCKET
from services.email_sender import send_email_with_attachment
import os
import tempfile

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
PDF_FOLDER = "summaries"
os.makedirs(PDF_FOLDER, exist_ok=True)


@app.route("/transcribe", methods=["POST"])
def transcribe_endpoint():
    """
    Lightweight endpoint: upload file + language -> returns transcript.
    Reuses previous simple behavior so it's backward compatible.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    language = request.form.get("language", "en")

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    transcript = transcribe_audio(file_path, language)
    return jsonify({"transcript": transcript})


@app.route("/process", methods=["POST"])
def process_meeting():
    """
    Full pipeline:
      - Accepts file (multipart/form-data)
      - language form field: "en" or "es"
      - send_email (optional boolean), email_to (if sending)
    Returns JSON with transcript, summary, tasks and presigned PDF URL.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    language = request.form.get("language", "en")
    send_email_flag = request.form.get("send_email", "false").lower() in ("1", "true", "yes")
    email_to = request.form.get("email_to", None)

    # Save uploaded audio locally
    local_audio_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(local_audio_path)

    # Step 1: Transcribe
    try:
        transcript = transcribe_audio(local_audio_path, language)
    except Exception as e:
        return jsonify({"error": f"Transcription failed: {e}"}), 500

    # Step 2: Summarize + extract tasks
    try:
        summary, tasks = generate_summary_and_tasks(transcript, language=language)
    except Exception as e:
        summary = ""
        tasks = ""
        # continue, we'll still create a PDF with transcript

    # Step 3: Create PDF locally
    metadata = {"language": language, "original_file": file.filename}
    pdf_filename = f"{os.path.splitext(file.filename)[0]}_summary.pdf"
    pdf_local_path = os.path.join(PDF_FOLDER, pdf_filename)
    create_meeting_pdf(transcript=transcript, summary=summary, tasks=tasks, output_path=pdf_local_path, metadata=metadata)

    # Step 4: Upload audio and PDF to MinIO
    try:
        audio_object = upload_file(local_audio_path, AUDIO_BUCKET, object_name=file.filename)
        pdf_object = upload_file(pdf_local_path, PDF_BUCKET, object_name=pdf_filename)
    except Exception as e:
        return jsonify({"error": f"Storage upload failed: {e}"}), 500

    # Step 5: Generate presigned URL for PDF
    try:
        pdf_url = get_presigned_url(PDF_BUCKET, pdf_object)
    except Exception as e:
        pdf_url = None

    # Step 6: Optionally send email with PDF attached
    if send_email_flag:
        if not email_to:
            return jsonify({"error": "send_email true but email_to not provided"}), 400
        try:
            subject = "Meeting Summary"
            body = f"Attached is the meeting summary for {file.filename}."
            send_email_with_attachment(email_to, subject, body, pdf_local_path, attachment_name=pdf_filename)
        except Exception as e:
            # don't fail whole pipeline; report the email error
            return jsonify({
                "transcript": transcript,
                "summary": summary,
                "tasks": tasks,
                "pdf_url": pdf_url,
                "email_sent": False,
                "email_error": str(e)
            }), 200

    # Return result
    return jsonify({
        "transcript": transcript,
        "summary": summary,
        "tasks": tasks,
        "pdf_url": pdf_url,
        "email_sent": send_email_flag
    }), 200


if __name__ == "__main__":
    # For development only. In production use gunicorn/uwsgi.
    app.run(host="0.0.0.0", port=5000, debug=True)
