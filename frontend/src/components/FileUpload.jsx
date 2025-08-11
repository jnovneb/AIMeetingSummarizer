import React, { useState } from "react";
import axios from "axios";
import ProgressBar from "./ProgressBar.jsx";

/**
 * FileUpload component:
 * - Select language
 * - Upload file with progress
 * - Optionally send email after processing
 * - Calls backend /process endpoint
 */

export default function FileUpload({ onResult }) {
  const [language, setLanguage] = useState("en");
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [sendEmail, setSendEmail] = useState(false);
  const [emailTo, setEmailTo] = useState("");
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setUploadProgress(0);
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!file) {
      setError("Please select an audio file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("language", language);
    formData.append("send_email", sendEmail ? "true" : "false");
    if (sendEmail && emailTo) {
      formData.append("email_to", emailTo);
    }

    setProcessing(true);
    setUploadProgress(0);

    try {
      const res = await axios.post("http://localhost:5000/process", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percent);
        },
        timeout: 120000 // 2 minutes (adjust as needed)
      });

      onResult(res.data);
    } catch (err) {
      console.error(err);
      setError(err?.response?.data?.error || err.message || "Upload failed");
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="card upload-card">
      <form onSubmit={handleSubmit}>
        <div className="row">
          <label>Language</label>
          <select value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="en">English</option>
            <option value="es">Español</option>
          </select>
        </div>

        <div className="row">
          <label>Choose audio</label>
          <input type="file" accept="audio/*" onChange={handleFileChange} />
        </div>

        <div className="row">
          <label>Send PDF by email?</label>
          <input type="checkbox" checked={sendEmail} onChange={(e) => setSendEmail(e.target.checked)} />
        </div>

        {sendEmail && (
          <div className="row">
            <label>Recipient email</label>
            <input type="email" value={emailTo} onChange={(e) => setEmailTo(e.target.value)} placeholder="name@example.com" />
          </div>
        )}

        <div className="row">
          <button type="submit" className="primary" disabled={processing}>
            {processing ? "Processing..." : "Upload & Process"}
          </button>
        </div>

        <div className="row">
          <ProgressBar value={uploadProgress} />
        </div>

        {error && <div className="error">{error}</div>}
      </form>
    </div>
  );
}
