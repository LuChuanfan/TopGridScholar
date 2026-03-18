from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncGenerator
from playwright.async_api import BrowserContext, Page
from models import Paper


class BaseScraper(ABC):
    """爬虫抽象基类"""

    def __init__(self, context: BrowserContext):
        self.context = context
        self._page: Page | None = None

    async def get_page(self) -> Page:
        """获取或创建页面"""
        if self._page is None or self._page.is_closed():
            self._page = await self.context.new_page()
        return self._page

    async def close_page(self):
        if self._page and not self._page.is_closed():
            await self._page.close()
            self._page = None

    @abstractmethod
    async def search(self, keyword: str, max_pages: int, progress: dict) -> AsyncGenerator[list[Paper], None]:
        """
        搜索论文，逐页 yield 结果。
        progress 字典用于实时更新进度信息。
        """
        ...

    @abstractmethod
    async def fetch_detail(self, paper: Paper) -> Paper:
        """获取论文详情（完整摘要、作者单位、PDF URL）"""
        ...

    @abstractmethod
    async def download_pdf(self, paper: Paper) -> bytes | None:
        """下载 PDF，返回字节流"""
        ...
