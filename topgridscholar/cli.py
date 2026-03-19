import sys
import os
import subprocess
import zipfile
import urllib.request
import re
from pathlib import Path

_GOOGLE_CDN = "https://storage.googleapis.com/chrome-for-testing-public"


def _parse_dry_run():
    """解析 playwright install --dry-run 输出，返回 [(name, install_path, download_url), ...]"""
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "--dry-run", "chromium"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None

    entries = []
    current_name = None
    current_path = None
    current_url = None

    for line in result.stdout.splitlines():
        # 新条目开头，如 "Chrome for Testing 145.0.7632.6 (playwright chromium v1208)"
        if line and not line.startswith(" "):
            if current_name and current_path and current_url:
                entries.append((current_name, current_path, current_url))
            current_name = line.strip()
            current_path = None
            current_url = None
        elif "Install location:" in line:
            current_path = Path(line.split("Install location:")[-1].strip())
        elif "Download url:" in line:
            current_url = line.split("Download url:")[-1].strip()

    if current_name and current_path and current_url:
        entries.append((current_name, current_path, current_url))

    return entries


def _download_with_progress(url, dest_path, desc=""):
    """用 Python urllib 下载文件，带进度显示和重试。"""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        try:
            print(f"  下载 {desc or url.split('/')[-1]} (尝试 {attempt}/{max_retries})...")
            req = urllib.request.Request(url, headers={"User-Agent": "TopGridScholar/0.1"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 256 * 1024  # 256KB

                with open(dest_path, "wb") as f:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = downloaded * 100 // total
                            mb = downloaded / 1024 / 1024
                            total_mb = total / 1024 / 1024
                            print(f"\r  {mb:.1f}/{total_mb:.1f} MB ({pct}%)", end="", flush=True)

            print()  # 换行
            return True
        except Exception as e:
            print(f"\n  下载失败: {e}")
            if dest_path.exists():
                dest_path.unlink()
            if attempt == max_retries:
                return False
    return False


def _to_google_cdn_url(original_url):
    """将 playwright CDN URL 转换为 Google CDN URL。"""
    # https://cdn.playwright.dev/chrome-for-testing-public/... -> https://storage.googleapis.com/chrome-for-testing-public/...
    # https://cdn.playwright.dev/dbazure/download/playwright/builds/... -> 保持不变（非 chrome-for-testing）
    if "chrome-for-testing-public/" in original_url:
        path = original_url.split("chrome-for-testing-public/", 1)[1]
        return f"{_GOOGLE_CDN}/{path}"
    return original_url


def _ensure_chromium():
    """检测 chromium 是否已安装，未安装则自动安装。"""
    entries = _parse_dry_run()
    if entries is None:
        return  # playwright 有问题，跳过

    # 检查是否全部已安装
    missing = [(name, path, url) for name, path, url in entries if not path.exists()]
    # 去重（FFmpeg 可能出现两次）
    seen_paths = set()
    unique_missing = []
    for name, path, url in missing:
        if str(path) not in seen_paths:
            seen_paths.add(str(path))
            unique_missing.append((name, path, url))

    if not unique_missing:
        return  # 全部已安装

    print("首次运行，正在自动安装 Chromium 浏览器...")
    print("First run, installing Chromium browser automatically...")
    print()

    # 先尝试 playwright install（默认 CDN）
    ret = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        timeout=180,
    )
    if ret.returncode == 0:
        print("\nChromium 安装完成！\n")
        return

    # 默认 CDN 失败，用 Python 自己下载（Google CDN）
    print()
    print("默认下载源失败，正在使用备用方式下载...")
    print("Default download failed, trying Python-based download...")
    print()

    import tempfile
    all_ok = True

    for name, install_path, original_url in unique_missing:
        if install_path.exists():
            continue  # 可能部分已安装

        # 优先用 Google CDN
        url = _to_google_cdn_url(original_url)

        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = Path(tmp_dir) / "download.zip"
            desc = name.split("(")[0].strip()

            if not _download_with_progress(url, zip_path, desc):
                # Google CDN 也失败，尝试原始 URL
                if url != original_url:
                    print(f"  备用源失败，尝试原始下载源...")
                    if not _download_with_progress(original_url, zip_path, desc):
                        all_ok = False
                        continue
                else:
                    all_ok = False
                    continue

            # 解压
            print(f"  解压中...")
            install_path.mkdir(parents=True, exist_ok=True)
            try:
                with zipfile.ZipFile(zip_path) as zf:
                    zf.extractall(install_path)
            except Exception as e:
                print(f"  解压失败: {e}")
                all_ok = False
                continue

            # 写入标记文件
            (install_path / "INSTALLATION_COMPLETE").touch()
            (install_path / "DEPENDENCIES_VALIDATED").touch()
            print(f"  {desc} 安装完成！")

    if all_ok:
        print("\nChromium 安装完成！\n")
    else:
        print()
        print("部分组件安装失败，请手动运行：")
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
