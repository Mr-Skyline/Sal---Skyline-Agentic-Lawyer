"""
Launch Elite Business Counsel — cross-platform.

  python launch.py          # start Streamlit + open browser
  python launch.py --no-browser   # start Streamlit only
"""
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get("STREAMLIT_PORT", "8501"))


def main() -> None:
    no_browser = "--no-browser" in sys.argv

    venv_py = ROOT / ".venv" / ("Scripts" if sys.platform == "win32" else "bin") / "python"
    python = str(venv_py) if venv_py.exists() else sys.executable

    cmd = [
        python, "-m", "streamlit", "run",
        str(ROOT / "main.py"),
        "--server.headless", "true",
        "--server.port", str(PORT),
    ]

    print(f"Starting Elite Business Counsel on http://localhost:{PORT}")
    proc = subprocess.Popen(cmd, cwd=str(ROOT))

    if not no_browser:
        time.sleep(3)
        webbrowser.open(f"http://localhost:{PORT}")

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        print("\nStopped.")


if __name__ == "__main__":
    main()
