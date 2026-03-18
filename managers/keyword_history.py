"""关键词历史管理：JSON 持久化，去重，最新在前。"""

import json
from pathlib import Path
from config import KEYWORD_HISTORY_FILE

MAX_HISTORY = 50


class KeywordHistory:

    def __init__(self, path: Path = KEYWORD_HISTORY_FILE):
        self._path = path
        self._history: list[str] = self._load()

    def _load(self) -> list[str]:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._history, ensure_ascii=False, indent=2), encoding="utf-8")

    def add(self, keyword: str):
        keyword = keyword.strip()
        if not keyword:
            return
        # 去重：如果已存在则移到最前
        if keyword in self._history:
            self._history.remove(keyword)
        self._history.insert(0, keyword)
        # 限制数量
        self._history = self._history[:MAX_HISTORY]
        self._save()

    def get_recent(self, n: int = 10) -> list[str]:
        return self._history[:n]

    def delete(self, keyword: str):
        keyword = keyword.strip()
        if keyword in self._history:
            self._history.remove(keyword)
            self._save()
