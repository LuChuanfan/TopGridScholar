import sys
import subprocess
from pathlib import Path


def main():
    pkg_dir = Path(__file__).resolve().parent
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"

    if cmd == "setup":
        subprocess.run([sys.executable, str(pkg_dir / "setup_browser.py")])
    else:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(pkg_dir / "app.py"),
            "--server.headless", "true",
        ])
