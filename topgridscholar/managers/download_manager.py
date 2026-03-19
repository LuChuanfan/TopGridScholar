from __future__ import annotations

import json
import asyncio
from pathlib import Path
from playwright.async_api import BrowserContext
from topgridscholar.config import DOWNLOAD_STATE_FILE, MAX_RETRY
from topgridscholar.models import Paper, DownloadTask, DownloadStatus
from topgridscholar.managers.file_organizer import FileOrganizer
from topgridscholar.scrapers.base import BaseScraper
from topgridscholar.scrapers.ieee import IEEEScraper
from topgridscholar.scrapers.nature import NatureScraper
from topgridscholar.scrapers.semantic_scholar import SemanticScholarScraper


class DownloadManager:
    """下载队列管理：持久化、断点续传、重试"""

    def __init__(self, state_file: Path = DOWNLOAD_STATE_FILE):
        self.state_file = state_file
        self.tasks: list[DownloadTask] = []
        self.organizer = FileOrganizer()
        self._paused = False
        self._cancelled = False
        self.load_state()

    # === 状态持久化 ===

    def save_state(self):
        data = [t.to_dict() for t in self.tasks]
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_state(self):
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                self.tasks = [DownloadTask.from_dict(d) for d in data]
            except Exception:
                self.tasks = []

    # === 队列操作 ===

    def add_papers(self, papers: list[Paper]):
        """添加论文到下载队列（去重）"""
        existing_urls = {t.paper.url for t in self.tasks if t.paper.url}
        for p in papers:
            if p.url and p.url not in existing_urls:
                self.tasks.append(DownloadTask(paper=p))
                existing_urls.add(p.url)
        self.save_state()

    def clear_completed(self):
        self.tasks = [t for t in self.tasks if t.status != DownloadStatus.COMPLETED]
        self.save_state()

    def remove_task(self, index: int):
        """删除指定索引的任务"""
        if 0 <= index < len(self.tasks):
            self.tasks.pop(index)
            self.save_state()

    def retry_all_failed(self):
        for t in self.tasks:
            if t.status == DownloadStatus.FAILED:
                t.status = DownloadStatus.PENDING
                t.error_message = ""
        self.save_state()

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def cancel(self):
        self._cancelled = True

    @property
    def stats(self) -> dict:
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == DownloadStatus.COMPLETED)
        failed = sum(1 for t in self.tasks if t.status == DownloadStatus.FAILED)
        pending = sum(1 for t in self.tasks if t.status == DownloadStatus.PENDING)
        in_progress = sum(1 for t in self.tasks if t.status in (
            DownloadStatus.FETCHING_DETAIL, DownloadStatus.DOWNLOADING
        ))
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "in_progress": in_progress,
        }

    # === 下载执行 ===

    async def run_downloads(self, context: BrowserContext, progress: dict):
        """执行下载队列"""
        self._paused = False
        self._cancelled = False
        progress["status"] = "running"

        ieee_scraper = IEEEScraper(context)
        nature_scraper = NatureScraper(context)
        ss_scraper = SemanticScholarScraper()

        for task in self.tasks:
            if self._cancelled:
                progress["status"] = "cancelled"
                break

            while self._paused:
                await asyncio.sleep(1)
                if self._cancelled:
                    break

            if task.status == DownloadStatus.COMPLETED:
                continue
            if task.status == DownloadStatus.FAILED and task.retry_count >= MAX_RETRY:
                continue

            # 根据来源选择爬虫
            source = task.paper.source
            if source == "IEEE":
                scraper = ieee_scraper
            elif source == "Nature":
                scraper = nature_scraper
            else:
                scraper = ss_scraper

            try:
                # 获取详情
                task.status = DownloadStatus.FETCHING_DETAIL
                progress["current_paper"] = task.paper.title
                progress["current_status"] = "获取详情..."
                self.save_state()

                task.paper = await scraper.fetch_detail(task.paper)

                # 下载 PDF
                task.status = DownloadStatus.DOWNLOADING
                progress["current_status"] = "下载PDF..."
                self.save_state()

                pdf_bytes = await scraper.download_pdf(task.paper)

                if pdf_bytes and len(pdf_bytes) > 1000:
                    save_path = self.organizer.get_save_path(task.paper)
                    save_path.write_bytes(pdf_bytes)
                    task.file_path = str(save_path)
                    task.status = DownloadStatus.COMPLETED
                else:
                    raise Exception("PDF 数据为空或过小（可能无 Open Access）")

            except Exception as e:
                task.retry_count += 1
                if task.retry_count >= MAX_RETRY:
                    task.status = DownloadStatus.FAILED
                    task.error_message = str(e)[:200]
                else:
                    task.status = DownloadStatus.PENDING
                    task.error_message = f"重试 {task.retry_count}/{MAX_RETRY}: {str(e)[:100]}"

            self.save_state()

        # 清理
        await ieee_scraper.close_page()
        await nature_scraper.close_page()
        await ss_scraper.close_page()

        if not self._cancelled:
            progress["status"] = "completed"
        progress["current_paper"] = ""
        progress["current_status"] = ""
