import React from 'react';
import './InvestigationNode.css';

// Function to get a color based on node status
const getStatusColor = (status) => {
  switch (status) {
    case 'confirmed': return '#28a745'; // Green
    case 'plausible': return '#ffc107'; // Yellow
    case 'implausible': return '#dc3545'; // Red
    case 'unverified':
    default: return '#6c757d'; // Gray
  }
};

const InvestigationNode = ({
  nodeDatum,
  toggleNode,
  foreignObjectProps,
  onUpdateStatus, // Receive handler from parent
  onGenerateNext, // Receive handler from parent
  onViewDetails, // Handler to view node details
  isSelected, // Whether this node is selected
}) => {
  const { title, description, type, status, confidence, metadata, locked } = nodeDatum;
  const nodeId = nodeDatum.id; // Use the actual node ID

  // Basic foreignObject properties, can be adjusted
  const nodeWidth = foreignObjectProps?.width ?? 200;
  const nodeHeight = foreignObjectProps?.height ?? 150;
  const x = -nodeWidth / 2;
  const y = -nodeHeight / 2;

  const handleMarkPlausible = (e) => {
    e.stopPropagation();
    if (onUpdateStatus) {
      onUpdateStatus(nodeId, 'plausible');
    } else {
      console.warn("onUpdateStatus handler not provided to InvestigationNode");
    }
  };

  const handleMarkImplausible = (e) => {
    e.stopPropagation();
    if (onUpdateStatus) {
      onUpdateStatus(nodeId, 'implausible');
    } else {
      console.warn("onUpdateStatus handler not provided to InvestigationNode");
    }
  };

  const handleGenerateNext = (e) => {
    e.stopPropagation();
    if (onGenerateNext) {
      onGenerateNext(nodeId);
    } else {
      console.warn("onGenerateNext handler not provided to InvestigationNode");
    }
  };
  
  const handleViewDetails = (e) => {
    e.stopPropagation();
    if (onViewDetails) {
      onViewDetails(nodeId);
    } else {
      console.warn("onViewDetails handler not provided to InvestigationNode");
    }
  };


  return (
    <foreignObject width={nodeWidth} height={nodeHeight} x={x} y={y}>
      <div
        className={`investigation-node ${isSelected ? 'selected' : ''} ${locked ? 'locked' : ''}`}
        style={{ borderTopColor: getStatusColor(status) }}
      >
        <div className="node-header">
          <span className="node-type">{type}</span>
          <span className="node-confidence">Conf: {(confidence * 100).toFixed(0)}%</span>
        </div>
        <h4 className="node-title">{title}</h4>
        <p className="node-description">{description}</p>
        {metadata?.reasoning && (
          <p className="node-reasoning">
            <em>Reasoning:</em> {metadata.reasoning.length > 60
              ? `${metadata.reasoning.substring(0, 60)}...`
              : metadata.reasoning}
          </p>
        )}

        <div className="node-buttons-container">
          {/* View Details Button - Always available for all nodes */}
          <button
            onClick={handleViewDetails}
            className="action-button details"
            title="View detailed information about this node"
          >
            View Details
          </button>

          {/* Interaction Buttons - Show based on node status */}
          {type !== 'root' && (
            <div className="node-actions">
              {/* Only show action buttons if the node is not locked and not marked as plausible/implausible */}
              {!locked && status !== 'plausible' && status !== 'implausible' && (
                <>
                  {/* Mark as plausible/implausible buttons */}
                  {(status === 'unverified' || status === 'confirmed') && (
                    <>
                      <button
                        onClick={handleMarkPlausible}
                        className="action-button plausible"
                        title="Mark this hypothesis as plausible and generate more hypotheses"
                      >
                        Plausible
                      </button>
                      <button
                        onClick={handleMarkImplausible}
                        className="action-button implausible"
                        title="Mark this hypothesis as implausible"
                      >
                        Implausible
                      </button>
                    </>
                  )}
                </>
              )}
            </div>
          )}
        </div>
        
        {/* Show locked indicator if the node is locked */}
        {locked && (
          <div className="locked-indicator">
            <span className="lock-icon">🔒</span>
            <span>Locked</span>
          </div>
        )}
      </div>
    </foreignObject>
  );
};

export default InvestigationNode;