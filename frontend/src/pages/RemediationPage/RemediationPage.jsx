import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  loadInvestigation,
  getBoardNodes,
  generatePerspectives,
  updatePerspectiveSelection,
  addUserInput,
  generateRoadmap
} from '../../services/remediationApi';
import BoardNode from './BoardNode.jsx';
import PerspectivePanel from './PerspectivePanel.jsx';
import RoadmapView from './RoadmapView.jsx';
import './RemediationPage.css';

function RemediationPage() {
  const { investigationId } = useParams();
  const navigate = useNavigate();
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [boardNodes, setBoardNodes] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [perspectives, setPerspectives] = useState(null);
  const [userInput, setUserInput] = useState('');
  const [showRoadmap, setShowRoadmap] = useState(false);
  const [roadmap, setRoadmap] = useState(null);

  // Load investigation data
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Load investigation tree from output directory
        const treePath = `output/investigation_tree_viz.json`;
        await loadInvestigation(treePath);
        
        const nodes = await getBoardNodes();
        setBoardNodes(nodes);
      } catch (err) {
        setError("Failed to load investigation data");
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadData();
  }, [investigationId]);

  // Handle node selection
  const handleNodeSelect = useCallback(async (nodeId) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const node = boardNodes.find(n => n.id === nodeId);
      setSelectedNode(node);
      setPerspectives(null);
      setUserInput('');
      
      const nodePerspectives = await generatePerspectives(nodeId);
      setPerspectives(nodePerspectives);
    } catch (err) {
      setError("Failed to load perspectives");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [boardNodes]);

  // Handle perspective selection
  const handlePerspectiveToggle = useCallback(async (perspectiveType, selected) => {
    if (!selectedNode) return;
    
    try {
      await updatePerspectiveSelection(selectedNode.id, perspectiveType, selected);
      setPerspectives(prev => ({
        ...prev,
        [perspectiveType]: {
          ...prev[perspectiveType],
          selected
        }
      }));
    } catch (err) {
      setError("Failed to update perspective");
      console.error(err);
    }
  }, [selectedNode]);

  // Handle user input
  const handleUserInputChange = (e) => {
    setUserInput(e.target.value);
  };

  const handleSaveUserInput = useCallback(async () => {
    if (!selectedNode || !userInput.trim()) return;
    
    try {
      await addUserInput(selectedNode.id, userInput);
    } catch (err) {
      setError("Failed to save notes");
      console.error(err);
    }
  }, [selectedNode, userInput]);

  // Generate roadmap
  const handleGenerateRoadmap = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const roadmapData = await generateRoadmap();
      console.log("Roadmap data received:", roadmapData);
      
      // Validate roadmap data
      if (!roadmapData || (!roadmapData.content && !roadmapData.raw_text)) {
        throw new Error("Invalid roadmap data received from server");
      }
      
      setRoadmap(roadmapData);
      setShowRoadmap(true);
    } catch (err) {
      setError(`Failed to generate roadmap: ${err.message || "Unknown error"}`);
      console.error("Roadmap generation error:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <div className="remediation-page">
      <header className="remediation-header">
        <h1>Remediation Advisor</h1>
        <button 
          className="generate-roadmap-btn"
          onClick={handleGenerateRoadmap}
          disabled={isLoading}
        >
          Generate Roadmap
        </button>
      </header>

      {isLoading && <div className="loading-overlay">Loading...</div>}
      {error && <div className="error-message">{error}</div>}

      <div className="remediation-container">
        <div className="board-container">
          {boardNodes.map(node => (
            <BoardNode
              key={node.id}
              node={node}
              isSelected={selectedNode?.id === node.id}
              onSelect={() => handleNodeSelect(node.id)}
            />
          ))}
        </div>

        {selectedNode && (
          <div className="details-panel">
            <h2>{selectedNode.title}</h2>
            <p className="node-description">{selectedNode.description}</p>
            
            {perspectives ? (
              <PerspectivePanel
                perspectives={perspectives}
                onToggle={handlePerspectiveToggle}
              />
            ) : (
              <div>Loading perspectives...</div>
            )}

            <div className="user-input-section">
              <h3>Your Notes</h3>
              <textarea
                value={userInput}
                onChange={handleUserInputChange}
                placeholder="Add your analysis or context..."
                rows={4}
              />
              <button
                onClick={handleSaveUserInput}
                disabled={!userInput.trim()}
              >
                Save Notes
              </button>
            </div>
          </div>
        )}
      </div>

      {showRoadmap && roadmap && (
        <RoadmapView
          roadmap={roadmap}
          onClose={() => setShowRoadmap(false)}
        />
      )}
    </div>
  );
}

export default RemediationPage;