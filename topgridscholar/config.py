from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# === 路径配置 ===
_DEFAULT_BASE_DIR = Path.cwd()
# 允许通过环境变量覆盖（方便把 data 放到别的盘）
BASE_DIR = Path(os.getenv("PAPERDOWNLOADER_BASE_DIR", str(_DEFAULT_BASE_DIR))).expanduser().resolve()
DATA_DIR = BASE_DIR / "data"
CHROME_PROFILE_DIR = DATA_DIR / "chrome_profile"
SESSIONS_DIR = DATA_DIR / "sessions"
DOWNLOADS_DIR = DATA_DIR / "downloads"
DOWNLOAD_STATE_FILE = DATA_DIR / "download_state.json"

# === 延迟配置（秒） ===
SEARCH_PAGE_DELAY = (10, 15)      # 搜索翻页间隔
DOWNLOAD_DELAY = (30, 60)         # 下载间隔
DETAIL_PAGE_DELAY = (5, 10)       # 详情页间隔

# === Chrome 配置 ===
BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-default-browser-check",
]

# === 文件命名 ===
MAX_FILENAME_LENGTH = 80
MAX_TITLE_LENGTH = 50

# === 下载 ===
MAX_RETRY = 3

# === IEEE ===
IEEE_SEARCH_URL = "https://ieeexplore.ieee.org/search/searchresult.jsp?queryText={keyword}&pageNumber={page}"
IEEE_PUB_SEARCH_URL = "https://ieeexplore.ieee.org/search/searchresult.jsp?queryText={keyword}&pageNumber={page}&searchWithin=%22Publication%20Title%22:{pub_title}"
IEEE_BASE_URL = "https://ieeexplore.ieee.org"

# === Nature ===
NATURE_SEARCH_URL = "https://www.nature.com/search?q={keyword}&page={page}&order=relevance"
NATURE_BASE_URL = "https://www.nature.com"

# === Semantic Scholar ===
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()
SEMANTIC_SCHOLAR_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

# === 关键词历史 ===
KEYWORD_HISTORY_FILE = DATA_DIR / "keyword_history.json"

# === 自动创建必要目录 ===
for _dir in (DATA_DIR, CHROME_PROFILE_DIR, SESSIONS_DIR, DOWNLOADS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
