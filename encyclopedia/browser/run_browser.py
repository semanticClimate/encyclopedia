#!/usr/bin/env python3
"""
Quick launcher for Encyclopedia Browser.

Usage:
    python run_browser.py
    python run_browser.py --port 8502
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Launch Streamlit browser app."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Launch Encyclopedia Browser")
    parser.add_argument(
        '--port',
        type=int,
        default=8501,
        help='Port to run Streamlit on (default: 8501)'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Path to encyclopedia HTML file to load automatically'
    )
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Check dependencies before launching'
    )
    
    args = parser.parse_args()
    
    # Check dependencies if requested
    if args.check_deps:
        check_script = Path(__file__).parent / "check_dependencies.py"
        if check_script.exists():
            print("Checking dependencies...")
            subprocess.run([sys.executable, str(check_script)], check=False)
            print()
    
    # Get path to app.py
    app_path = Path(__file__).parent / "app.py"
    
    if not app_path.exists():
        print(f"Error: Could not find app.py at {app_path}")
        sys.exit(1)
    
    # Build command
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(args.port)
    ]
    
    if args.file:
        cmd.extend(["--", "--file", args.file])
    
    print(f"Launching Encyclopedia Browser on port {args.port}...")
    print(f"Using Python: {sys.executable}")
    print(f"Open http://localhost:{args.port} in your browser")
    print()
    
    # Run Streamlit
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nBrowser stopped.")
    except Exception as e:
        print(f"Error launching browser: {e}")
        print("\nTip: Run with --check-deps to diagnose dependency issues:")
        print(f"  python {Path(__file__).name} --check-deps")
        sys.exit(1)


if __name__ == "__main__":
    main()
