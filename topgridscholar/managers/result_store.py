from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import pandas as pd
from topgridscholar.config import SESSIONS_DIR
from topgridscholar.models import Paper


class ResultStore:
    """搜索结果保存/加载(JSON)、元数据导出(CSV)"""

    def __init__(self, sessions_dir: Path = SESSIONS_DIR):
        self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def save_session(self, keyword: str, source: str, papers: list[Paper]) -> Path:
        """保存搜索会话为 JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_keyword = "".join(c if c.isalnum() or c in " _-" else "_" for c in keyword)[:30]
        filename = f"{timestamp}_{safe_keyword}.json"
        path = self.sessions_dir / filename

        data = {
            "keyword": keyword,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "count": len(papers),
            "papers": [p.to_dict() for p in papers],
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load_session(self, path: Path) -> tuple[str, str, list[Paper]]:
        """加载搜索会话，返回 (keyword, source, papers)"""
        data = json.loads(path.read_text(encoding="utf-8"))
        papers = [Paper.from_dict(p) for p in data.get("papers", [])]
        return data.get("keyword", ""), data.get("source", ""), papers

    def list_sessions(self) -> list[dict]:
        """列出所有保存的会话"""
        sessions = []
        for f in sorted(self.sessions_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                sessions.append({
                    "path": str(f),
                    "filename": f.name,
                    "keyword": data.get("keyword", ""),
                    "source": data.get("source", ""),
                    "count": data.get("count", 0),
                    "timestamp": data.get("timestamp", ""),
                })
            except Exception:
                continue
        return sessions

    @staticmethod
    def export_csv(papers: list[Paper], path: Path):
        """导出论文元数据为 CSV（utf-8-sig 编码，Excel 兼容）"""
        rows = []
        for p in papers:
            authors_str = "; ".join(
                f"{a.name} ({a.affiliation})" if a.affiliation else a.name
                for a in p.authors
            )
            rows.append({
                "标题": p.title,
                "作者": authors_str,
                "期刊": p.journal,
                "年份": p.year,
                "DOI": p.doi,
                "摘要": p.abstract,
                "来源URL": p.url,
                "来源": p.source,
            })
        df = pd.DataFrame(rows)
        df.to_csv(path, index=False, encoding="utf-8-sig")
