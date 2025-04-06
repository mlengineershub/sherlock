import React from 'react';
import './PerspectivePanel.css';

// Define paths to perspective icons
const expertIcon = '/assets/images/expert.png';
const attackerIcon = '/assets/images/hacker.png';
const businessIcon = '/assets/images/business.png';
const legalIcon = '/assets/images/legal.png';

function PerspectivePanel({ perspectives, onToggle }) {
  // Map perspective types to their respective icons
  const perspectiveIcons = {
    expert: expertIcon,
    attacker: attackerIcon,
    business: businessIcon,
    compliance: legalIcon
  };
  if (!perspectives) return null;

  const renderPerspective = (type, perspective) => {
    if (!perspective) return null;
    
    return (
      <div
        key={type}
        className={`perspective-card ${type} ${perspective.selected ? 'selected' : ''}`}
      >
        <div className="perspective-header">
          <div className="perspective-title">
            <img
              src={perspectiveIcons[type]}
              alt={`${type} icon`}
              className="perspective-icon"
            />
            <h4>{perspective.title}</h4>
          </div>
          <div className="perspective-actions">
            <button
              className={`accept-button ${perspective.selected ? 'active' : ''}`}
              onClick={() => onToggle(type, true)}
              title="Accept this perspective"
            >
              ✓
            </button>
            <button
              className={`reject-button ${perspective.selected === false ? 'active' : ''}`}
              onClick={() => onToggle(type, false)}
              title="Reject this perspective"
            >
              ✗
            </button>
          </div>
        </div>
        <div className="perspective-content">
          {perspective.content}
        </div>
      </div>
    );
  };
  
  return (
    <div className="perspectives-panel">
      <h3>Multiple Perspectives Analysis</h3>
      <div className="perspectives-grid">
        {perspectives.expert && renderPerspective('expert', perspectives.expert)}
        {perspectives.attacker && renderPerspective('attacker', perspectives.attacker)}
        {perspectives.business && renderPerspective('business', perspectives.business)}
        {perspectives.compliance && renderPerspective('compliance', perspectives.compliance)}
      </div>
    </div>
  );
}

export default PerspectivePanel;