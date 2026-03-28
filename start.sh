#!/bin/bash

# Auto Register Tasks - Service Starter

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

show_help() {
    echo "Auto Register Tasks - Service Starter"
    echo ""
    echo "Usage: ./start.sh [command]"
    echo ""
    echo "Commands:"
    echo "  api         Start FastAPI server (port 8000)"
    echo "  web         Start Gradio web interface (port 7860)"
    echo "  all         Start both API and Web services"
    echo "  install     Install dependencies"
    echo "  test        Run tests"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./start.sh api          # Start API server only"
    echo "  ./start.sh web          # Start web interface only"
    echo "  ./start.sh all          # Start both services"
}

install_deps() {
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo "Installing Playwright browsers..."
    playwright install chromium
    echo "Done!"
}

run_tests() {
    echo "Running tests..."
    pytest tests/ -v
}

start_api() {
    echo "Starting FastAPI server on http://0.0.0.0:8000"
    cd "$PROJECT_DIR"
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
}

start_web() {
    echo "Starting Gradio web interface on http://0.0.0.0:7860"
    cd "$PROJECT_DIR"
    python -m web.app
}

start_all() {
    echo "Starting all services..."
    start_api &
    API_PID=$!
    sleep 2
    start_web &
    WEB_PID=$!
    
    echo ""
    echo "Services started:"
    echo "  API:   http://localhost:8000"
    echo "  Web:   http://localhost:7860"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    trap "kill $API_PID $WEB_PID 2>/dev/null; exit" INT TERM
    
    wait
}

case "${1:-help}" in
    api)
        start_api
        ;;
    web)
        start_web
        ;;
    all)
        start_all
        ;;
    install)
        install_deps
        ;;
    test)
        run_tests
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
