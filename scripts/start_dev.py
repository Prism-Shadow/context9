#!/usr/bin/env python3
"""
Development server startup script.
Starts both backend and frontend development servers.
"""

import subprocess
import sys
import signal
import time
from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
GUI_DIR = PROJECT_ROOT / "gui"
BACKEND_SCRIPT = PROJECT_ROOT / "context9" / "server.py"


def start_backend(args):
    """Start backend server."""
    print("🚀 Starting backend server...")
    backend_cmd = [
        sys.executable,
        "-m",
        "context9.server",
        "--github_sync_interval",
        str(args.github_sync_interval),
        "--config_file",
        args.config_file,
        "--port",
        str(args.port),
    ]
    return subprocess.Popen(backend_cmd, cwd=PROJECT_ROOT)


def start_frontend():
    """Start frontend development server."""
    print("🚀 Starting frontend development server...")
    # Check if node_modules exists
    if not (GUI_DIR / "node_modules").exists():
        print("📦 Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=GUI_DIR, check=True)

    frontend_cmd = ["npm", "run", "dev"]
    return subprocess.Popen(frontend_cmd, cwd=GUI_DIR)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Start Context9 development servers (backend + frontend)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--enable_github_webhook", action="store_true", help="Enable GitHub webhook"
    )
    group.add_argument(
        "--github_sync_interval",
        type=int,
        default=600,
        help="GitHub sync interval in seconds",
    )
    parser.add_argument(
        "--config_file",
        type=str,
        required=True,
        help="Config file path",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8011,
        help="Backend server port",
    )
    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="Only start frontend (backend must be running separately)",
    )
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="Only start backend (frontend must be running separately)",
    )

    args = parser.parse_args()

    processes = []

    def cleanup(signum, frame):
        """Cleanup function to kill all child processes."""
        print("\n🛑 Shutting down servers...")
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            except Exception:
                pass
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        if not args.frontend_only:
            backend_proc = start_backend(args)
            processes.append(backend_proc)
            print("✅ Backend server started")
            time.sleep(2)  # Wait for backend to start

        if not args.backend_only:
            frontend_proc = start_frontend()
            processes.append(frontend_proc)
            print("✅ Frontend server started")
            print("\n📝 Servers running:")
            if not args.frontend_only:
                print(f"   Backend: http://localhost:{args.port}")
            if not args.backend_only:
                print("   Frontend: http://localhost:3000")
            print("\nPress Ctrl+C to stop all servers")

        # Wait for all processes
        for proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        cleanup(None, None)
    except Exception as e:
        print(f"❌ Error: {e}")
        cleanup(None, None)


if __name__ == "__main__":
    main()
