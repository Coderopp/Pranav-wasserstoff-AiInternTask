#!/bin/bash

# Function to handle script termination
cleanup() {
    echo "Shutting down services..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Set up trap to catch termination signal
trap cleanup SIGINT SIGTERM

# Print colorful messages
print_message() {
    echo -e "\e[1;34m$1\e[0m"
}

# Check if Python and Node.js are installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "backend/venv" ]; then
    print_message "Creating Python virtual environment..."
    python3 -m venv backend/venv
fi

# Activate virtual environment and install backend dependencies
print_message "Setting up backend..."
source backend/venv/bin/activate
pip install -r backend/requirements.txt

# Install frontend dependencies
print_message "Setting up frontend..."
cd frontend
npm install
cd ..

# Start backend server
print_message "Starting backend server..."
source backend/venv/bin/activate
cd backend
python -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend development server
print_message "Starting frontend development server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

print_message "Both servers are running!"
print_message "Backend: http://localhost:8000"
print_message "Frontend: http://localhost:3000"
print_message "Press Ctrl+C to stop both servers"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 