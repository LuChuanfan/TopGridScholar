import sys
import os
import subprocess
import zipfile
import urllib.request
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
                chunk_size = 256 * 1024

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

            print()
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
    if "chrome-for-testing-public/" in original_url:
        path = original_url.split("chrome-for-testing-public/", 1)[1]
        return f"{_GOOGLE_CDN}/{path}"
    return original_url


def _python_download(unique_missing):
    """用 Python urllib 下载并安装所有缺失的组件。"""
    import tempfile
    all_ok = True

    for name, install_path, original_url in unique_missing:
        if install_path.exists():
            continue

        # 优先用 Google CDN
        url = _to_google_cdn_url(original_url)

        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = Path(tmp_dir) / "download.zip"
            desc = name.split("(")[0].strip()

            if not _download_with_progress(url, zip_path, desc):
                # Google CDN 失败，尝试原始 URL
                if url != original_url:
                    print(f"  备用源失败，尝试原始下载源...")
                    if not _download_with_progress(original_url, zip_path, desc):
                        all_ok = False
                        continue
                else:
                    all_ok = False
                    continue

            print(f"  解压中...")
            install_path.mkdir(parents=True, exist_ok=True)
            try:
                with zipfile.ZipFile(zip_path) as zf:
                    zf.extractall(install_path)
            except Exception as e:
                print(f"  解压失败: {e}")
                all_ok = False
                continue

            (install_path / "INSTALLATION_COMPLETE").touch()
            (install_path / "DEPENDENCIES_VALIDATED").touch()
            print(f"  {desc} 安装完成！")

    return all_ok


def _ensure_chromium():
    """检测 chromium 是否已安装，未安装则自动安装。"""
    entries = _parse_dry_run()
    if entries is None:
        return

    missing = [(name, path, url) for name, path, url in entries if not path.exists()]
    seen_paths = set()
    unique_missing = []
    for name, path, url in missing:
        if str(path) not in seen_paths:
            seen_paths.add(str(path))
            unique_missing.append((name, path, url))

    if not unique_missing:
        return

    print("=" * 60)
    print("  首次运行，正在自动安装 Chromium 浏览器...")
    print("  First run, installing Chromium browser automatically...")
    print()
    print("  请耐心等待，下载约 280MB，不要关闭此窗口。")
    print("  Please wait patiently, downloading ~280MB.")
    print("  如果某个下载源失败，会自动尝试其他方式，无需手动操作。")
    print("  If one method fails, it will automatically try another.")
    print("=" * 60)
    print()

    # 优先使用 Python 下载器（兼容性更好，国内网络更稳定）
    if _python_download(unique_missing):
        print("\nChromium 安装完成！\n")
        return

    # Python 下载器失败，尝试 playwright install 作为备用
    print()
    print("备用方式下载中，请继续等待...")
    print("Trying alternative download method, please wait...")
    print()

    ret = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        timeout=300,
    )
    if ret.returncode == 0:
        print("\nChromium 安装完成！\n")
        return

    print()
    print("Chromium 自动安装失败，请手动运行：")
    print("  playwright install chromium")
    print()
    print("如果下载超时，可尝试设置代理后重试：")
    print("  set HTTPS_PROXY=http://127.0.0.1:你的代理端口")
    print("  playwright install chromium")
    sys.exit(1)


def _ensure_streamlit_config():
    """创建 Streamlit 配置文件，跳过首次运行的邮箱提示。"""
    config_dir = Path.home() / ".streamlit"
    credentials_file = config_dir / "credentials.toml"
    if not credentials_file.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
        credentials_file.write_text('[general]\nemail = ""\n', encoding="utf-8")


def main():
    pkg_dir = Path(__file__).resolve().parent
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"

    if cmd == "setup":
        _ensure_chromium()
        subprocess.run([sys.executable, str(pkg_dir / "setup_browser.py")])
    else:
        _ensure_chromium()
        _ensure_streamlit_config()
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(pkg_dir / "app.py"),
        ])
