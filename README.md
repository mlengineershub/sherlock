# SecAI Investigation Agent

A modern security breach investigation tool with an interactive visualization interface.

## Features

- Interactive investigation tree visualization
- AI-powered hypothesis generation
- Node expansion for deeper investigation
- Detailed node information view
- Investigation report generation
- Modern, responsive UI

## Project Structure

- `frontend/`: React-based frontend application
- `backend/`: Python-based backend services
  - `common/`: Shared utilities and services
  - `investigation/`: Investigation agent and tree management

## Running the Application

### Backend

1. Start the backend API server:

```bash
python -m backend.investigation.run_api
```

The API server will run on http://localhost:8000

### Frontend

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

The frontend will be available at http://localhost:5173

## Usage

1. Enter initial breach information in the text area
2. Click "Start Investigation" to generate the initial investigation tree
3. Interact with nodes:
   - Click "View Details" to see detailed information about a node
   - Click "Expand" to generate more hypotheses based on the selected node
   - Click "Plausible" to mark a node as plausible and automatically expand it
   - Click "Implausible" to mark a node as implausible and lock it
4. Click "Generate Report" to create a comprehensive investigation report

## Technologies Used

- Frontend: React, Vite, react-d3-tree
- Backend: Python, FastAPI, AWS Bedrock (Claude AI models)
