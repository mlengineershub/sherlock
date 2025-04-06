import React from 'react';
import './RoadmapView.css';

function RoadmapView({ roadmap, onClose }) {
  console.log("Roadmap data received:", roadmap);

  const parseRoadmapContent = () => {
    try {
      // Check if roadmap has the expected structure
      if (!roadmap || !roadmap.raw_text) {
        console.error("Invalid roadmap data structure:", roadmap);
        return (
          <div className="roadmap-error">
            <h3>Error Parsing Roadmap</h3>
            <p>The roadmap data is not in the expected format.</p>
          </div>
        );
      }

      // Use raw_text for parsing if content is not available
      const content = roadmap.content || roadmap.raw_text;
      
      // Simple parser for the roadmap text content
      const sections = content.split('\n\n');
      return sections.map((section, index) => {
        if (section.startsWith('1.')) {
          return (
            <div key={`immediate-${index}`} className="roadmap-section immediate">
              <h3>Immediate Actions (Next 24-48 hours)</h3>
              <div className="section-content">
                {section.substring(2).trim()}
              </div>
            </div>
          );
        } else if (section.startsWith('2.')) {
          return (
            <div key={`short-term-${index}`} className="roadmap-section short-term">
              <h3>Short-term Actions (Next Week)</h3>
              <div className="section-content">
                {section.substring(2).trim()}
              </div>
            </div>
          );
        } else if (section.startsWith('3.')) {
          return (
            <div key={`medium-term-${index}`} className="roadmap-section medium-term">
              <h3>Medium-term Actions (Next Month)</h3>
              <div className="section-content">
                {section.substring(2).trim()}
              </div>
            </div>
          );
        }
        return (
          <div key={`other-${index}`} className="roadmap-section">
            <div className="section-content">
              {section.trim()}
            </div>
          </div>
        );
      });
    } catch (error) {
      console.error("Error parsing roadmap content:", error);
      return (
        <div className="roadmap-error">
          <h3>Error Parsing Roadmap</h3>
          <p>{error.message || "An unexpected error occurred while parsing the roadmap."}</p>
        </div>
      );
    }
  };

  return (
    <div className="roadmap-modal">
      <div className="roadmap-content">
        <div className="roadmap-header">
          <h2>Remediation Roadmap</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        <div className="roadmap-body">
          {parseRoadmapContent()}
        </div>
        <div className="roadmap-footer">
          <button className="export-btn">Export as PDF</button>
          <button className="close-btn" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

export default RoadmapView;