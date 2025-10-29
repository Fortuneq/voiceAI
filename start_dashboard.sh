#!/bin/bash
# VoiceAI Dashboard Startup Script

echo "🎯 VoiceAI Call Analysis Dashboard"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "src/api_server.py" ]; then
    echo "❌ Please run this script from the VoiceAI project root directory"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "💡 Consider activating your Python virtual environment first"
    echo ""
fi

# Install Python dependencies if needed
echo "📦 Checking Python dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Start backend server in background
echo "🚀 Starting FastAPI backend server..."
python -m uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "❌ Frontend directory not found. Please ensure the frontend was created properly."
    kill $BACKEND_PID
    exit 1
fi

# Install frontend dependencies if needed
echo "📦 Checking frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📥 Installing frontend dependencies..."
    npm install
fi

# Start frontend server
echo "⚛️  Starting React frontend server..."
npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo "=================================="
echo "🎉 VoiceAI Dashboard is running!"
echo "📊 Dashboard: http://localhost:3000"
echo "🔌 API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "=================================="
echo ""
echo "💡 Press Ctrl+C to stop all servers"

# Function to handle cleanup
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Shutdown complete"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Wait for processes
while kill -0 $BACKEND_PID 2>/dev/null && kill -0 $FRONTEND_PID 2>/dev/null; do
    sleep 1
done

echo "❌ One or more servers have stopped"
cleanup