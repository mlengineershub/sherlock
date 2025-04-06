/**
 * API service for connecting to the backend
 */

const API_BASE_URL = '/api'; // Adjust this based on your deployment setup

/**
 * Start a new investigation with the provided breach information
 * @param {string} breachInfo - Description of the security breach
 * @returns {Promise<Object>} - The investigation tree data
 */
export async function startInvestigation(breachInfo) {
  try {
    const response = await fetch(`${API_BASE_URL}/investigation/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ breach_info: breachInfo }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to start investigation:', error);
    throw error;
  }
}

/**
 * Update the status of a node in the investigation tree
 * @param {string} nodeId - ID of the node to update
 * @param {string} status - New status for the node (plausible, implausible, confirmed)
 * @returns {Promise<boolean>} - Success indicator
 */
export async function updateNodeStatus(nodeId, status) {
  try {
    const response = await fetch(`${API_BASE_URL}/investigation/node/${nodeId}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ status }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Failed to update node ${nodeId} status:`, error);
    throw error;
  }
}

/**
 * Generate the next level of nodes for a given parent node
 * @param {string} parentId - ID of the parent node
 * @param {number} numNodes - Number of nodes to generate (default: 3)
 * @returns {Promise<Array>} - Array of generated node IDs
 */
export async function generateNextLevel(parentId, numNodes = 3) {
  try {
    const response = await fetch(`${API_BASE_URL}/investigation/node/${parentId}/expand`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ num_nodes: numNodes }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Failed to generate next level for node ${parentId}:`, error);
    throw error;
  }
}

/**
 * Get the current investigation tree
 * @returns {Promise<Object>} - The current investigation tree data
 */
export async function getInvestigationTree() {
  try {
    const response = await fetch(`${API_BASE_URL}/investigation/tree`);

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to get investigation tree:', error);
    throw error;
  }
}

/**
 * Generate a report from the current investigation
 * @returns {Promise<Object>} - The generated report
 */
export async function generateReport() {
  try {
    const response = await fetch(`${API_BASE_URL}/investigation/report`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to generate report:', error);
    throw error;
  }
}

/**
 * Get node details including evidence and expanded description
 * @param {string} nodeId - ID of the node to get details for
 * @returns {Promise<Object>} - Detailed node information
 */
export async function getNodeDetails(nodeId) {
  try {
    const response = await fetch(`${API_BASE_URL}/investigation/node/${nodeId}/details`);

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Failed to get details for node ${nodeId}:`, error);
    throw error;
  }
}