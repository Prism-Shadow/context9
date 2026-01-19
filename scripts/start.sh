#!/bin/bash
# Development startup script for Context9
# Starts both backend and frontend servers

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GUI_DIR="$PROJECT_ROOT/gui"

# Parse arguments
ENABLE_WEBHOOK=false
SYNC_INTERVAL=600
CONFIG_FILE=""
PORT=8011
FRONTEND_ONLY=false
BACKEND_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --enable_github_webhook)
            ENABLE_WEBHOOK=true
            shift
            ;;
        --github_sync_interval)
            SYNC_INTERVAL="$2"
            shift 2
            ;;
        --config_file)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --frontend-only)
            FRONTEND_ONLY=true
            shift
            ;;
        --backend-only)
            BACKEND_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ -z "$CONFIG_FILE" ]; then
    echo "Error: --config_file is required"
    exit 1
fi

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
if [ "$FRONTEND_ONLY" = false ]; then
    echo "🚀 Starting backend server..."
    cd "$PROJECT_ROOT"
    if [ "$ENABLE_WEBHOOK" = true ]; then
        uv run python -m context9.server \
            --enable_github_webhook \
            --config_file "$CONFIG_FILE" \
            --port "$PORT" &
    else
        uv run python -m context9.server \
            --github_sync_interval "$SYNC_INTERVAL" \
            --config_file "$CONFIG_FILE" \
            --port "$PORT" &
    fi
    BACKEND_PID=$!
    echo "✅ Backend server started (PID: $BACKEND_PID)"
    sleep 2
fi

# Start frontend
if [ "$BACKEND_ONLY" = false ]; then
    echo "🚀 Starting frontend development server..."
    cd "$GUI_DIR"
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install
    fi
    
    npm run dev &
    FRONTEND_PID=$!
    echo "✅ Frontend server started (PID: $FRONTEND_PID)"
fi

echo ""
echo "📝 Servers running:"
if [ "$FRONTEND_ONLY" = false ]; then
    echo "   Backend: http://localhost:$PORT"
fi
if [ "$BACKEND_ONLY" = false ]; then
    echo "   Frontend: http://localhost:3000"
fi
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for processes
wait
