import React from "react";

/**
 * Simple, aesthetic progress bar component
 */
export default function ProgressBar({ value = 0 }) {
  return (
    <div className="progress-outer" aria-hidden>
      <div className="progress-inner" style={{ width: `${value}%` }}>
        <span className="progress-label">{value}%</span>
      </div>
    </div>
  );
}
