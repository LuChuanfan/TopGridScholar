"""Semantic Scholar API 爬虫，用于 CCF-A/B 期刊和会议搜索。"""
from __future__ import annotations

import asyncio
import aiohttp
from typing import AsyncGenerator
from topgridscholar.models import Paper, Author
from topgridscholar.config import SEMANTIC_SCHOLAR_API_KEY, SEMANTIC_SCHOLAR_SEARCH_URL

# API 每次最多返回 100 条
_PAGE_SIZE = 100
_FIELDS = "title,authors,year,abstract,venue,externalIds,url,openAccessPdf"


class SemanticScholarScraper:
    """不需要浏览器，纯 API 请求。"""

    def __init__(self, venue_fullnames: list[str] | None = None):
        # 没有 key 时仍可尝试匿名额度；若 API 返回 401/403 会给出友好状态
        self._headers = {"x-api-key": SEMANTIC_SCHOLAR_API_KEY} if SEMANTIC_SCHOLAR_API_KEY else {}
        # 本地二次过滤白名单（小写化，用于精确匹配）
        self._venue_whitelist: set[str] | None = None
        if venue_fullnames:
            self._venue_whitelist = {v.lower() for v in venue_fullnames}

    async def search(self, keyword: str, max_pages: int, progress: dict,
                     venues: list[str] | None = None) -> AsyncGenerator[list[Paper], None]:
        """
        搜索论文，逐页 yield。
        max_pages: 每页 100 条，max_pages=3 即最多 300 条。
        venues: Semantic Scholar venue 名称列表，用逗号拼接传给 API。
        """
        progress.update({"current_page": 0, "total_pages": max_pages, "found": 0, "status": "searching"})

        async with aiohttp.ClientSession(headers=self._headers) as session:
            for page_num in range(1, max_pages + 1):
                progress["current_page"] = page_num
                offset = (page_num - 1) * _PAGE_SIZE

                params = {
                    "query": keyword,
                    "offset": offset,
                    "limit": _PAGE_SIZE,
                    "fields": _FIELDS,
                }
                if venues:
                    params["venue"] = ",".join(venues)

                try:
                    async with session.get(SEMANTIC_SCHOLAR_SEARCH_URL, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        if resp.status != 200:
                            if resp.status in (401, 403):
                                progress["status"] = "Semantic Scholar API 认证失败：请设置环境变量 SEMANTIC_SCHOLAR_API_KEY"
                            else:
                                progress["status"] = f"API 错误: HTTP {resp.status}"
                            break
                        data = await resp.json()

                    papers = self._parse_results(data.get("data", []))
                    # 本地二次过滤：确保 venue 全称在白名单中
                    if self._venue_whitelist:
                        papers = [p for p in papers if p.journal.lower() in self._venue_whitelist]
                    progress["found"] = progress.get("found", 0) + len(papers)
                    yield papers

                    # 没有更多结果
                    if data.get("next") is None:
                        break

                    # API 限速：每秒最多 10 次
                    await asyncio.sleep(0.2)

                except asyncio.TimeoutError:
                    progress["status"] = f"第{page_num}页超时"
                    continue
                except Exception as e:
                    progress["status"] = f"第{page_num}页出错: {str(e)[:100]}"
                    continue

        progress["status"] = "completed"

    def _parse_results(self, items: list[dict]) -> list[Paper]:
        papers = []
        for item in items:
            title = item.get("title", "")
            if not title:
                continue

            authors = []
            for a in item.get("authors", []):
                name = a.get("name", "")
                if name:
                    authors.append(Author(name=name))

            external_ids = item.get("externalIds") or {}
            doi = external_ids.get("DOI", "")

            # 尝试获取 open access PDF
            pdf_info = item.get("openAccessPdf") or {}
            pdf_url = pdf_info.get("url", "") or ""

            paper = Paper(
                title=title,
                authors=authors,
                journal=item.get("venue", ""),
                year=str(item.get("year", "")),
                abstract=item.get("abstract", "") or "",
                doi=doi,
                url=item.get("url", ""),
                pdf_url=pdf_url,
                source="Semantic Scholar",
            )
            papers.append(paper)

        return papers

    async def close_page(self):
        """兼容接口，API 爬虫无需关闭页面。"""
        pass

    async def fetch_detail(self, paper: Paper) -> Paper:
        """API 搜索已包含摘要等信息，无需额外请求。"""
        return paper

    async def download_pdf(self, paper: Paper) -> bytes | None:
        """通过 open access PDF URL 下载。"""
        if not paper.pdf_url:
            return None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(paper.pdf_url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200 and "pdf" in resp.headers.get("content-type", ""):
                        return await resp.read()
        except Exception:
            pass
        return None
