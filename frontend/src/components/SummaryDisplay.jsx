import React from "react";

/**
 * SummaryDisplay shows transcript, summary, tasks and links to download PDF.
 * Expects `result` object returned by /process endpoint.
 */
export default function SummaryDisplay({ result }) {
  const { transcript, summary, tasks, pdf_url, email_sent } = result || {};

  return (
    <div className="card result-card">
      <div className="result-header">
        <h2>Summary</h2>
        <div className="actions">
          {pdf_url ? (
            <a className="btn" href={pdf_url} target="_blank" rel="noreferrer">Download PDF</a>
          ) : (
            <button className="btn disabled">PDF not available</button>
          )}
        </div>
      </div>

      <section className="section">
        <h3>Short Summary</h3>
        <p className="summary-text">{summary || "No summary generated."}</p>
      </section>

      <section className="section">
        <h3>Action Items</h3>
        <pre className="tasks-block">{tasks || "No tasks detected."}</pre>
      </section>

      <section className="section">
        <h3>Transcript</h3>
        <div className="transcript-block">{transcript || "No transcript."}</div>
      </section>

      <footer className="result-footer">
        <small>{email_sent ? "Email sent." : "Email not sent."}</small>
      </footer>
    </div>
  );
}
