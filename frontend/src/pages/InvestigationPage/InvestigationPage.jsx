import React, { useState, useCallback, useEffect } from 'react';
import Tree from 'react-d3-tree';
import InvestigationNode from './InvestigationNode'; // Import the custom node
import './InvestigationPage.css';
import {
  startInvestigation,
  updateNodeStatus,
  generateNextLevel,
  getInvestigationTree,
  generateReport,
  getNodeDetails
} from '../../services/api';


function InvestigationPage() {
  const [breachInfo, setBreachInfo] = useState('');
  const [treeData, setTreeData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [nodeRenderKey, setNodeRenderKey] = useState(0); // Key to force re-render
  const [selectedNode, setSelectedNode] = useState(null);
  const [nodeDetails, setNodeDetails] = useState(null);
  const [showReport, setShowReport] = useState(false);
  const [report, setReport] = useState(null);
  const [translate, setTranslate] = useState({ x: window.innerWidth / 2, y: 80 });

  // Handle window resize to keep the tree centered
  useEffect(() => {
    const handleResize = () => {
      setTranslate({ x: window.innerWidth / 2, y: 80 });
      setNodeRenderKey(prev => prev + 1); // Force re-render on resize
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Helper function to recursively find and update/add nodes in the tree data
  const updateTreeNode = (nodes, targetId, updateFn) => {
    if (!nodes) return null;

    // Check if current node is the target
    if (nodes.id === targetId) {
      return updateFn(nodes);
    }

    // Recursively search in children
    if (nodes.children) {
      let updated = false;
      const newChildren = nodes.children.map(child => {
        const updatedChild = updateTreeNode(child, targetId, updateFn);
        if (updatedChild !== child) {
          updated = true; // Mark if a child was updated
        }
        return updatedChild;
      });

      // If children were updated, return a new node object with updated children
      if (updated) {
        return { ...nodes, children: newChildren };
      }
    }

    // If target not found in this branch, return the original node
    return nodes;
  };

  const handleStartInvestigation = useCallback(async () => {
    if (!breachInfo.trim()) {
      setError('Please provide initial breach information.');
      return;
    }
    setIsLoading(true);
    setError(null);
    setTreeData(null); // Clear previous tree
    setSelectedNode(null);
    setNodeDetails(null);
    setShowReport(false);
    setReport(null);

    try {
      // Call the actual backend API
      const data = await startInvestigation(breachInfo);
      setTreeData(data);
    } catch (err) {
      console.error("Investigation failed:", err);
      setError('Failed to start investigation. Please check console.');
    } finally {
      setIsLoading(false);
    }
  }, [breachInfo]);

  // Handler to update node status
  const handleUpdateNodeStatus = useCallback(async (nodeId, newStatus) => {
    try {
      setIsLoading(true);
      console.log(`Updating node ${nodeId} to status: ${newStatus}`);
      
      // Call the backend API to update node status
      await updateNodeStatus(nodeId, newStatus);
      
      // If the node is marked as implausible or plausible, lock it
      if (newStatus === 'implausible' || newStatus === 'plausible') {
        setTreeData(prevTreeData => {
          if (!prevTreeData) return null;
          return updateTreeNode(prevTreeData, nodeId, (node) => ({
            ...node,
            status: newStatus,
            locked: true // Add a locked flag
          }));
        });
        
        // If the node is marked as plausible, automatically generate next level
        if (newStatus === 'plausible') {
          await handleGenerateNextLevel(nodeId);
        }
      } else {
        // For other statuses, just update the status
        setTreeData(prevTreeData => {
          if (!prevTreeData) return null;
          return updateTreeNode(prevTreeData, nodeId, (node) => ({
            ...node,
            status: newStatus,
          }));
        });
      }
      
      // Force re-render
      setNodeRenderKey(prev => prev + 1);
    } catch (err) {
      console.error(`Failed to update node status: ${err}`);
      setError(`Failed to update node status: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Handler to generate next level
  const handleGenerateNextLevel = useCallback(async (parentId) => {
    try {
      setIsLoading(true);
      console.log(`Generating next level for parent: ${parentId}`);
      
      // Call the backend API to generate next level
      const response = await generateNextLevel(parentId);
      
      // Refresh the tree data after expansion
      const updatedTreeData = await getInvestigationTree();
      setTreeData(updatedTreeData);
      
      // Force re-render
      setNodeRenderKey(prev => prev + 1);
    } catch (err) {
      console.error(`Failed to generate next level: ${err}`);
      setError(`Failed to generate next level: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  // Handler to view node details
  const handleViewNodeDetails = useCallback(async (nodeId) => {
    try {
      setIsLoading(true);
      console.log(`Getting details for node: ${nodeId}`);
      
      // Call the backend API to get node details
      const details = await getNodeDetails(nodeId);
      setSelectedNode(nodeId);
      setNodeDetails(details);
    } catch (err) {
      console.error(`Failed to get node details: ${err}`);
      setError(`Failed to get node details: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  // Handler to generate report
  const handleGenerateReport = useCallback(async () => {
    try {
      setIsLoading(true);
      console.log("Generating investigation report");
      
      // Call the backend API to generate report
      const reportData = await generateReport();
      setReport(reportData);
      setShowReport(true);
    } catch (err) {
      console.error(`Failed to generate report: ${err}`);
      setError(`Failed to generate report: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  // Close the report modal
  const handleCloseReport = useCallback(() => {
    setShowReport(false);
  }, []);
  
  // Close the node details panel
  const handleCloseDetails = useCallback(() => {
    setSelectedNode(null);
    setNodeDetails(null);
  }, []);

  // Define properties for the foreignObject wrapper required by react-d3-tree
  const foreignObjectProps = { width: 280, height: 240, x: -140, y: -25 }; // Increased height for better button visibility

  return (
    <div className="investigation-page">
      <header className="app-header">
        <h1>SecAI Investigation Agent 🕵️</h1>
        {treeData && (
          <button
            className="report-button"
            onClick={handleGenerateReport}
            disabled={isLoading}
          >
            Generate Report
          </button>
        )}
      </header>

      <div className="main-content">
        <div className="investigation-controls">
          <h2>Security Breach Investigation</h2>
          <textarea
            value={breachInfo}
            onChange={(e) => setBreachInfo(e.target.value)}
            placeholder="Enter initial breach information (e.g., suspicious login activity, system alert details)..."
            rows={4}
            disabled={isLoading}
          />
          <button
            className="primary-button"
            onClick={handleStartInvestigation}
            disabled={isLoading || !breachInfo.trim()}
          >
            {isLoading ? 'Investigating...' : 'Start Investigation'}
          </button>
          {error && <p className="error-message">{error}</p>}
        </div>

        <div className="visualization-container">
          <div className="tree-container">
            {isLoading && <div className="loading-overlay"><div className="loader"></div></div>}
            {treeData && (
              <Tree
                data={treeData}
                orientation="vertical"
                pathFunc="step"
                translate={translate}
                separation={{ siblings: 2, nonSiblings: 2.5 }}
                nodeSize={{ x: 300, y: 250 }}
                centeringTransitionDuration={800}
                renderCustomNodeElement={(rd3tProps) => (
                  <InvestigationNode
                    {...rd3tProps}
                    foreignObjectProps={foreignObjectProps}
                    onUpdateStatus={handleUpdateNodeStatus}
                    onGenerateNext={handleGenerateNextLevel}
                    onViewDetails={handleViewNodeDetails}
                    isSelected={rd3tProps.nodeDatum.id === selectedNode}
                  />
                )}
                key={nodeRenderKey}
              />
            )}
            {!isLoading && !treeData && !error && (
              <div className="placeholder-container">
                <p className="placeholder-text">Enter breach information and click "Start Investigation" to see the analysis tree.</p>
                <div className="placeholder-icon">🔍</div>
              </div>
            )}
          </div>
          
          {nodeDetails && (
            <div className="details-panel">
              <h3>Node Details</h3>
              <div className="details-content">
                <h4>{nodeDetails.title}</h4>
                <div className="detail-item">
                  <span className="detail-label">Type:</span>
                  <span className="detail-value">{nodeDetails.type}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Status:</span>
                  <span className={`detail-value status-${nodeDetails.status}`}>{nodeDetails.status}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Confidence:</span>
                  <span className="detail-value">{(nodeDetails.confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="detail-item full-width">
                  <span className="detail-label">Description:</span>
                  <p className="detail-value description">{nodeDetails.description}</p>
                </div>
                {nodeDetails.evidence && nodeDetails.evidence.length > 0 && (
                  <div className="detail-item full-width">
                    <span className="detail-label">Evidence:</span>
                    <ul className="evidence-list">
                      {nodeDetails.evidence.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {nodeDetails.metadata && Object.keys(nodeDetails.metadata).length > 0 && (
                  <div className="detail-item full-width">
                    <span className="detail-label">Additional Information:</span>
                    <div className="metadata">
                      {Object.entries(nodeDetails.metadata).map(([key, value]) => (
                        <div key={key} className="metadata-item">
                          <span className="metadata-key">{key}:</span>
                          <span className="metadata-value">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <button className="close-button" onClick={handleCloseDetails}>Close</button>
            </div>
          )}
        </div>
      </div>
      
      {/* Report Modal */}
      {showReport && (
        <div className="modal-overlay">
          <div className="report-modal">
            <button className="modal-close" onClick={handleCloseReport}>×</button>
            <h2>{report.title}</h2>
            <div className="report-content">
              <h3>Summary</h3>
              <p className="report-summary">{report.summary}</p>
              
              <h3>Findings</h3>
              <div className="findings-list">
                {report.findings.map((finding, index) => (
                  <div key={index} className="finding-item">
                    <h4>{finding.title}</h4>
                    <p>{finding.description}</p>
                    <div className="finding-meta">
                      <span className={`finding-status status-${finding.status}`}>{finding.status}</span>
                      <span className="finding-confidence">Confidence: {(finding.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
              
              <h3>Recommendations</h3>
              <ul className="recommendations-list">
                {report.recommendations.map((rec, index) => (
                  <li key={index}>{rec}</li>
                ))}
              </ul>
              
              <div className="report-footer">
                <p>Report generated: {new Date(report.timestamp).toLocaleString()}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default InvestigationPage;