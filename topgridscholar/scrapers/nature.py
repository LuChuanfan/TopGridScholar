from __future__ import annotations

import re
import asyncio
from typing import AsyncGenerator
from urllib.parse import quote_plus
from playwright.async_api import BrowserContext, Page
from topgridscholar.models import Paper, Author
from topgridscholar.scrapers.base import BaseScraper
from topgridscholar.scrapers.anti_scraping import anti_scraping_pause, random_delay, human_scroll
from topgridscholar.config import (
    NATURE_SEARCH_URL, NATURE_BASE_URL,
    SEARCH_PAGE_DELAY, DETAIL_PAGE_DELAY, DOWNLOAD_DELAY,
)


class NatureScraper(BaseScraper):

    # 需要过滤掉的期刊（小写）
    EXCLUDED_JOURNALS = {"scientific reports"}

    def __init__(self, context: BrowserContext):
        super().__init__(context)

    async def search(self, keyword: str, max_pages: int, progress: dict) -> AsyncGenerator[list[Paper], None]:
        page = await self.get_page()
        progress.update({"current_page": 0, "total_pages": max_pages, "found": 0, "status": "searching"})

        for page_num in range(1, max_pages + 1):
            progress["current_page"] = page_num
            url = NATURE_SEARCH_URL.format(keyword=quote_plus(keyword), page=page_num)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_selector("article.c-card", timeout=15000)
                await human_scroll(page)

                papers = await self._parse_search_results(page)
                # 过滤掉排除的期刊
                papers = [p for p in papers if p.journal.lower() not in self.EXCLUDED_JOURNALS]
                progress["found"] = progress.get("found", 0) + len(papers)
                yield papers

                if not await self._has_next_page(page):
                    break

                if page_num < max_pages:
                    await anti_scraping_pause(page, SEARCH_PAGE_DELAY)

            except Exception as e:
                progress["status"] = f"第{page_num}页出错: {str(e)[:100]}"
                await random_delay(5, 10)
                continue

        progress["status"] = "completed"

    async def _parse_search_results(self, page: Page) -> list[Paper]:
        papers = []
        items = await page.query_selector_all("article.c-card")

        for item in items:
            try:
                paper = Paper(title="", source="Nature")

                # 标题
                title_el = await item.query_selector("h3 a, .c-card__title a, a[data-track-action='search result']")
                if title_el:
                    paper.title = (await title_el.inner_text()).strip()
                    href = await title_el.get_attribute("href")
                    if href:
                        paper.url = NATURE_BASE_URL + href if href.startswith("/") else href

                if not paper.title:
                    continue

                # 作者
                author_list = await item.query_selector_all("ul[data-test='author-list'] li span[itemprop='name']")
                for a_el in author_list:
                    name = (await a_el.inner_text()).strip()
                    if name:
                        paper.authors.append(Author(name=name))

                # 期刊名
                journal_el = await item.query_selector("div[data-test='journal-title-and-link']")
                if journal_el:
                    paper.journal = (await journal_el.inner_text()).strip()

                # 年份
                date_el = await item.query_selector("time[itemprop='datePublished']")
                if date_el:
                    date_text = await date_el.get_attribute("datetime") or await date_el.inner_text()
                    year_match = re.search(r'(20\d{2}|19\d{2})', date_text)
                    if year_match:
                        paper.year = year_match.group(1)

                papers.append(paper)
            except Exception:
                continue

        return papers

    async def _has_next_page(self, page: Page) -> bool:
        # Nature 的分页结构: <li data-page="next"> <a>...</a> </li>
        # 有 a 标签说明可点击（非 disabled）
        next_link = await page.query_selector("li[data-page='next'] a")
        return next_link is not None

    async def fetch_detail(self, paper: Paper) -> Paper:
        if not paper.url:
            return paper

        page = await self.get_page()
        try:
            await page.goto(paper.url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_selector("#Abs1-content, .c-article-section__content, .article__body", timeout=15000)
            await human_scroll(page)

            # 摘要
            abs_el = await page.query_selector("#Abs1-content, div[id*='Abs'] .c-article-section__content")
            if abs_el:
                paper.abstract = (await abs_el.inner_text()).strip()

            # DOI (meta 标签)
            doi_meta = await page.query_selector("meta[name='citation_doi'], meta[name='DOI']")
            if doi_meta:
                doi_val = await doi_meta.get_attribute("content")
                if doi_val:
                    paper.doi = doi_val

            # 期刊名（从 meta 标签获取更可靠）
            if not paper.journal:
                journal_meta = await page.query_selector("meta[name='citation_journal_title']")
                if journal_meta:
                    paper.journal = (await journal_meta.get_attribute("content")) or ""

            # 构建 作者→单位 映射（从 affiliation 列表）
            aff_map: dict[str, str] = {}  # aff_id -> address
            aff_items = await page.query_selector_all("ol.c-article-author-affiliation__list li")
            for li in aff_items:
                aff_id = await li.get_attribute("id") or ""
                addr_el = await li.query_selector(".c-article-author-affiliation__address")
                if addr_el:
                    aff_map[aff_id] = (await addr_el.inner_text()).strip()

            # 作者+单位
            author_items = await page.query_selector_all("ul[data-test='authors-list'] li")
            if author_items:
                new_authors = []
                for li in author_items:
                    name_el = await li.query_selector("a[data-test='author-name']")
                    if not name_el:
                        continue
                    name = (await name_el.inner_text()).strip()
                    if not name:
                        continue

                    # 从 href 中提取 Aff ID（如 #auth-Jun-Liu-Aff1 或 #auth-Yang-Zhang-Aff1-Aff2-Aff3）
                    aff = ""
                    href = await name_el.get_attribute("href") or ""
                    aff_ids = re.findall(r'Aff\d+', href)
                    if aff_ids and aff_map:
                        affs = [aff_map[aid] for aid in aff_ids if aid in aff_map]
                        aff = "; ".join(affs)

                    new_authors.append(Author(name=name, affiliation=aff))
                if new_authors:
                    paper.authors = new_authors

            # PDF URL
            pdf_link = await page.query_selector("a[data-article-pdf]")
            if pdf_link:
                href = await pdf_link.get_attribute("href")
                if href:
                    paper.pdf_url = NATURE_BASE_URL + href if href.startswith("/") else href

            await anti_scraping_pause(page, DETAIL_PAGE_DELAY)

        except Exception:
            pass

        return paper

    async def download_pdf(self, paper: Paper) -> bytes | None:
        if not paper.pdf_url and not paper.url:
            return None

        page = await self.get_page()
        pdf_bytes = None

        async def handle_response(response):
            nonlocal pdf_bytes
            try:
                content_type = response.headers.get("content-type", "")
                status = response.status
                if "application/pdf" in content_type and status == 200:
                    body = await response.body()
                    if body and len(body) > 1000:
                        pdf_bytes = body
            except Exception:
                pass

        async def wait_for_pdf(timeout=30):
            for _ in range(timeout * 2):
                if pdf_bytes is not None:
                    return True
                await asyncio.sleep(0.5)
            return False

        page.on("response", handle_response)

        try:
            pdf_url = paper.pdf_url
            if not pdf_url and paper.url:
                pdf_url = paper.url.rstrip("/") + ".pdf"

            await page.goto(pdf_url, wait_until="domcontentloaded", timeout=60000)
            await wait_for_pdf(timeout=30)

            await anti_scraping_pause(page, DOWNLOAD_DELAY)

        except Exception:
            pass
        finally:
            page.remove_listener("response", handle_response)

        return pdf_bytes
