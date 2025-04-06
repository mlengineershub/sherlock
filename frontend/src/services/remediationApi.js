/**
 * Service for interacting with the remediation advisory API
 */
import axios from 'axios';

// Use port 8001 for remediation API as shown in the logs
const API_URL = import.meta.env.VITE_REMEDIATION_API_URL || 'http://localhost:8001';

export const loadInvestigation = async (treePath, documentationPath = null) => {
  const response = await axios.post(`${API_URL}/api/remediation/load`, {
    tree_path: treePath,
    documentation_path: documentationPath
  });
  return response.data;
};

export const getBoardNodes = async () => {
  const response = await axios.get(`${API_URL}/api/remediation/board`);
  return response.data;
};

export const generatePerspectives = async (nodeId) => {
  const response = await axios.post(
    `${API_URL}/api/remediation/node/${nodeId}/perspectives`
  );
  return response.data;
};

export const updatePerspectiveSelection = async (nodeId, perspectiveType, selected) => {
  const response = await axios.put(
    `${API_URL}/api/remediation/node/${nodeId}/perspective/${perspectiveType}`,
    { selected }
  );
  return response.data;
};

export const addUserInput = async (nodeId, content) => {
  const response = await axios.put(
    `${API_URL}/api/remediation/node/${nodeId}/input`,
    { content }
  );
  return response.data;
};

export const generateRoadmap = async () => {
  const response = await axios.post(`${API_URL}/api/remediation/roadmap`);
  return response.data;
};

// Add response interceptors for error handling
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data);
    } else {
      console.error('API Connection Error:', error.message);
    }
    return Promise.reject(error);
  }
);