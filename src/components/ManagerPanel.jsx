import React from 'react';
import './ManagerPanel.css';

// Accepts an array of image paths to render manager portraits only from assets/
// Example usage:
// <ManagerPanel images={["assets/manager_1.png","assets/manager_2.png"]} />
export default function ManagerPanel({ images = [] }) {
  return (
    <section className="manager-panel" aria-label="Manager panel using assets">
      <header className="panel-header">
        <span className="brand">PREDERBY</span>
        <span className="league">Premier League • 2025/26</span>
      </header>

      <div className="panel-content">
        {images.map((src, idx) => (
          <div className="card" key={idx} aria-label={`Manager ${idx + 1}`}>
            <img src={src} alt={`Manager portrait ${idx + 1}`} />
          </div>
        ))}
      </div>
    </section>
  );
}
