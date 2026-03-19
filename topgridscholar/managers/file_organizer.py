import re
from pathlib import Path
from topgridscholar.config import DOWNLOADS_DIR, MAX_FILENAME_LENGTH, MAX_TITLE_LENGTH
from topgridscholar.models import Paper


class FileOrganizer:
    """文件命名与组织：来源/完整标题_作者姓_年份.pdf"""

    def __init__(self, base_dir: Path = DOWNLOADS_DIR):
        self.base_dir = base_dir

    def get_save_path(self, paper: Paper) -> Path:
        # 按来源分类存储
        source = paper.source or "Other"
        if source == "Semantic Scholar":
            source = "CCF-AB"

        title = self._sanitize(paper.title)
        surname = self._sanitize(paper.first_author_surname())
        year = paper.year or "Unknown"

        filename = f"{title}_{surname}_{year}.pdf"
        # Windows 文件路径最长 260，留余量给目录部分
        if len(filename) > 200:
            filename = f"{title[:150]}_{surname}_{year}.pdf"

        save_dir = self.base_dir / source
        save_dir.mkdir(parents=True, exist_ok=True)
        return save_dir / filename

    @staticmethod
    def _sanitize(name: str) -> str:
        """清理 Windows 文件名非法字符"""
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        name = re.sub(r'\s+', ' ', name).strip()
        name = name.strip('. ')
        return name or "Unknown"
