import React from 'react';
import './BoardNode.css';

function BoardNode({ node, isSelected, onSelect }) {
  const getNodeClass = () => {
    let className = 'board-node';
    className += ` type-${node.type.toLowerCase()}`;
    className += ` status-${node.status.toLowerCase()}`;
    if (isSelected) className += ' selected';
    return className;
  };

  return (
    <div 
      className={getNodeClass()}
      onClick={onSelect}
    >
      <div className="node-header">
        <h3 className="node-title">{node.title}</h3>
        <span className="node-confidence">
          {Math.round(node.confidence * 100)}%
        </span>
      </div>
      <div className="node-type">{node.type}</div>
    </div>
  );
}

export default BoardNode;