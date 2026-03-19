import sys
import os
import subprocess
from pathlib import Path

# Google CDN 在国内可直连，作为 Playwright 默认 CDN 的备选
_GOOGLE_CDN = "https://storage.googleapis.com/chrome-for-testing-public"


def _ensure_chromium():
    """检测 chromium 是否已安装，未安装则自动安装。"""
    # 用 dry-run 检查安装路径是否存在
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "--dry-run", "chromium"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        # playwright 本身有问题，跳过检测让后续流程报错
        return

    for line in result.stdout.splitlines():
        if "Install location:" in line:
            install_path = Path(line.split("Install location:")[-1].strip())
            if install_path.exists():
                return  # 已安装
            break

    print("首次运行，正在自动安装 Chromium 浏览器...")
    print("First run, installing Chromium browser automatically...")
    print()

    # 先尝试默认 CDN
    ret = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        timeout=120,
    )
    if ret.returncode == 0:
        print()
        print("Chromium 安装完成！")
        return

    # 默认 CDN 失败，尝试 Google CDN 镜像
    print()
    print("默认下载源失败，正在尝试备用下载源...")
    print("Default download failed, trying alternative mirror...")
    print()

    env = os.environ.copy()
    env["PLAYWRIGHT_DOWNLOAD_HOST"] = _GOOGLE_CDN
    ret = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        env=env,
        timeout=300,
    )
    if ret.returncode == 0:
        print()
        print("Chromium 安装完成！")
    else:
        print()
        print("Chromium 自动安装失败，请手动运行：")
        print("  playwright install chromium")
        print()
        print("如果下载超时，可尝试设置代理后重试：")
        print("  set HTTPS_PROXY=http://127.0.0.1:你的代理端口")
        print("  playwright install chromium")
        sys.exit(1)


def main():
    pkg_dir = Path(__file__).resolve().parent
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"

    if cmd == "setup":
        _ensure_chromium()
        subprocess.run([sys.executable, str(pkg_dir / "setup_browser.py")])
    else:
        _ensure_chromium()
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(pkg_dir / "app.py"),
            "--server.headless", "true",
        ])
