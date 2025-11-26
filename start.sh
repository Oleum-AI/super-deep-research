#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Deep Research Services...${NC}"
echo ""

# Sync dependencies
echo -e "${BLUE}Syncing Python dependencies...${NC}"
cd backend && uv sync
cd ..

# Install UI dependencies
echo -e "${BLUE}Installing UI dependencies...${NC}"
if [ -d "frontend" ]; then
    cd frontend
    npm install
    cd ..
else
    echo -e "${YELLOW}Frontend directory not found. Skipping frontend dependencies.${NC}"
fi

# Load environment variables from .env if it exists
if [ -f backend/.env ]; then
  export $(grep -v '^#' backend/.env | xargs)
  echo -e "${GREEN}Loaded environment variables from backend/.env${NC}"
else
  # Default configuration if .env doesn't exist
  export BACKEND_PORT=8001
  export FRONTEND_PORT=5173
  echo -e "${GREEN}Using default port configuration: API=$BACKEND_PORT, UI=$FRONTEND_PORT${NC}"
fi

# Set variables for this script
API_PORT=$BACKEND_PORT
UI_PORT=$FRONTEND_PORT

# Check if API port is already in use
if lsof -i:$API_PORT > /dev/null 2>&1; then
  echo -e "${YELLOW} ⚠️ Port $API_PORT is already in use. Stopping the process...${NC}"
  kill -9 $(lsof -t -i:$API_PORT) || echo -e "${RED} ❌ Failed to kill process on port $API_PORT${NC}"
  sleep 2
fi

# Check if UI port is already in use
if lsof -i:$UI_PORT > /dev/null 2>&1; then
  echo -e "${YELLOW} ⚠️ Port $UI_PORT is already in use. Stopping the process...${NC}"
  kill -9 $(lsof -t -i:$UI_PORT) || echo -e "${RED} ❌ Failed to kill process on port $UI_PORT${NC}"
  sleep 2
fi

# Start the FastAPI backend
echo -e "${BLUE}▶️  Starting Backend API (PORT=$API_PORT)...${NC}"
cd backend
API_PORT=$API_PORT uv run python main.py &
API_PID=$!
echo -e "${GREEN}✅ Backend PROCESS_ID=$API_PID${NC}"
cd ..

# Start the React frontend
if [ -d "frontend" ]; then
    echo -e "${BLUE}▶️  Starting Frontend (PORT=$UI_PORT)...${NC}"
    cd frontend && npm run dev &
    UI_PID=$!
    echo -e "${GREEN}✅ Frontend PROCESS_ID=$UI_PID${NC}"
    cd ..
else
    echo -e "${YELLOW}Frontend not set up yet. Only running backend.${NC}"
    UI_PID=""
fi

echo ""
echo -e "${GREEN}Services are running!"
echo "API is available at: http://localhost:$API_PORT"
echo "UI is available at: http://localhost:$UI_PORT"
echo "API health endpoint: http://localhost:$API_PORT/api/health"
echo -e "Press Ctrl+C to stop both services ${NC}"

# Handle clean shutdown
function cleanup {
  echo ""
  echo -e "${RED}Stopping services...${NC}"
  kill $API_PID 2>/dev/null
  if [ ! -z "$UI_PID" ]; then
    kill $UI_PID 2>/dev/null
  fi
  exit 0
}

trap cleanup SIGINT

# Wait for processes
wait