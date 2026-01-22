#!/usr/bin/env python3
"""
Startup script for launching Context9 in production mode.

This script supports:
- Loading environment variables from .env file in project root directory
- Specifying command-line arguments for server.py (--config_file, --enable_github_webhook, --github_sync_interval)
- Setting environment variables via command-line (CONTEXT9_PORT, CONTEXT9_PANEL_PORT)
- Building frontend for production and launching backend server (which serves the frontend static files)
"""

import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
GUI_DIR = PROJECT_ROOT / "gui"


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Start Context9 in production mode (builds frontend and starts backend server)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Arguments for server.py
    parser.add_argument(
        "--config_file",
        type=str,
        default=None,
        help="Config file path (passed to server.py)",
    )

    webhook_group = parser.add_mutually_exclusive_group()
    webhook_group.add_argument(
        "--enable_github_webhook",
        action="store_true",
        help="Enable GitHub webhook (passed to server.py)",
    )
    webhook_group.add_argument(
        "--github_sync_interval",
        type=int,
        default=None,
        help="GitHub sync interval in seconds (passed to server.py)",
    )

    # Environment variable arguments
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Backend server port (sets CONTEXT9_PORT environment variable)",
    )
    parser.add_argument(
        "--panel_port",
        type=int,
        default=None,
        help="Frontend panel port (sets CONTEXT9_PANEL_PORT environment variable, not used in production)",
    )
    parser.add_argument(
        "--skip_build",
        action="store_true",
        help="Skip frontend build step (use existing build if available)",
    )
    parser.add_argument(
        "--log_level",
        type=str,
        default="INFO",
        help="Log level",
    )

    return parser.parse_args()


def build_server_command(args):
    """Build backend server startup command"""
    cmd = [sys.executable, "-m", "context9.server"]

    if args.config_file:
        cmd.extend(["--config_file", args.config_file])

    if args.enable_github_webhook:
        cmd.append("--enable_github_webhook")
    elif args.github_sync_interval is not None:
        cmd.extend(["--github_sync_interval", str(args.github_sync_interval)])
    else:
        # If webhook or sync_interval is not specified, default to sync_interval
        cmd.extend(["--github_sync_interval", "600"])

    if args.log_level:
        cmd.extend(["--log_level", args.log_level])

    return cmd


def build_frontend():
    """Build frontend for production"""
    print("Building frontend for production...")
    # Set VITE_API_BASE_URL to empty string for production mode
    # This makes the frontend use relative paths (same origin) since backend serves both API and frontend
    env = os.environ.copy()
    env["VITE_API_BASE_URL"] = ""  # Use relative paths in production
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=GUI_DIR,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("Frontend build failed")
    print("Frontend build completed successfully")


def check_frontend_build():
    """Check if frontend build exists"""
    dist_path = GUI_DIR / "dist"
    index_path = dist_path / "index.html"
    return dist_path.exists() and index_path.exists()


def setup_environment(args):
    """Setup environment variables"""
    # Load environment variables from .env file in project root
    # load_dotenv will silently do nothing if the file doesn't exist
    load_dotenv(PROJECT_ROOT / ".env")

    env = os.environ.copy()

    if args.port:
        env["CONTEXT9_PORT"] = str(args.port)

    if args.panel_port:
        env["CONTEXT9_PANEL_PORT"] = str(args.panel_port)

    return env


def main():
    """Main function"""
    args = parse_args()

    # Setup environment variables
    env = setup_environment(args)

    # Build frontend if needed
    if not args.skip_build:
        build_frontend()
    else:
        if not check_frontend_build():
            print("Warning: Frontend build not found. Building frontend...")
            build_frontend()
        else:
            print("Using existing frontend build (--skip_build specified)")

    # Build backend command
    backend_cmd = build_server_command(args)

    print("=" * 60)
    print("Starting Context9 in Production Mode")
    print("=" * 60)
    print(f"Backend command: {' '.join(backend_cmd)}")
    if env.get("CONTEXT9_PORT"):
        print(f"Server port: {env.get('CONTEXT9_PORT')}")
    print("Frontend: Served as static files by backend server")
    print("=" * 60)
    print()

    # Store process objects
    processes = []

    def signal_handler(sig, frame):
        """Signal handler for graceful shutdown"""
        print("\nReceived shutdown signal, stopping server...")
        for proc in processes:
            if proc.poll() is None:  # Process is still running
                proc.terminate()
        # Wait for processes to terminate
        for proc in processes:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start backend server (which also serves frontend static files)
        print("Starting backend server...")
        backend_proc = subprocess.Popen(
            backend_cmd,
            env=env,
            cwd=PROJECT_ROOT,
        )
        processes.append(backend_proc)

        print("\nContext9 server is running in production mode!")
        print("Backend API and frontend are available on the same port.")
        print("Press Ctrl+C to stop the server\n")

        # Wait for process to finish
        backend_proc.wait()

    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        signal_handler(signal.SIGTERM, None)
        sys.exit(1)


if __name__ == "__main__":
    main()
