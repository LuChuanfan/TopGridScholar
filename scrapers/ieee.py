from __future__ import annotations

import re
import asyncio
from typing import AsyncGenerator
from urllib.parse import quote_plus
from playwright.async_api import BrowserContext, Page
from models import Paper, Author
from scrapers.base import BaseScraper
from scrapers.anti_scraping import anti_scraping_pause, random_delay, human_scroll
from config import (
    IEEE_SEARCH_URL, IEEE_PUB_SEARCH_URL, IEEE_BASE_URL,
    SEARCH_PAGE_DELAY, DETAIL_PAGE_DELAY, DOWNLOAD_DELAY,
)


class IEEEScraper(BaseScraper):

    def __init__(self, context: BrowserContext):
        super().__init__(context)

    async def search(self, keyword: str, max_pages: int, progress: dict,
                     pub_titles: list[str] | None = None) -> AsyncGenerator[list[Paper], None]:
        """
        搜索论文。
        pub_titles: 如果提供，则逐期刊搜索（每个期刊搜 max_pages 页），结果精准。
                    如果为 None，则普通搜索。
        """
        page = await self.get_page()

        if pub_titles:
            # 逐期刊搜索模式
            total_journals = len(pub_titles)
            progress.update({"current_page": 0, "total_pages": total_journals,
                             "found": 0, "status": "searching"})

            for j_idx, pub_title in enumerate(pub_titles):
                progress["current_page"] = j_idx + 1
                progress["current_journal"] = pub_title

                for page_num in range(1, max_pages + 1):
                    url = IEEE_PUB_SEARCH_URL.format(
                        keyword=quote_plus(keyword), page=page_num, pub_title=quote_plus(pub_title))

                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                        await page.wait_for_selector(
                            "xpl-results-list .List-results-items, .no-results-message",
                            timeout=20000)

                        # 检查是否无结果
                        no_results = await page.query_selector(".no-results-message, .List-results-items")
                        if no_results:
                            tag = await no_results.evaluate("el => el.tagName")
                            if tag and "no-results" in (await no_results.get_attribute("class") or "").lower():
                                break

                        await human_scroll(page)
                        papers = await self._parse_search_results(page)
                        if not papers:
                            break

                        progress["found"] = progress.get("found", 0) + len(papers)
                        yield papers

                        if not await self._has_next_page(page):
                            break

                        if page_num < max_pages:
                            await anti_scraping_pause(page, SEARCH_PAGE_DELAY)

                    except Exception as e:
                        progress["status"] = f"{pub_title[:30]}... 第{page_num}页出错: {str(e)[:80]}"
                        await random_delay(5, 10)
                        break  # 这个期刊出错就跳到下一个

                # 期刊间延迟
                if j_idx < total_journals - 1:
                    await anti_scraping_pause(page, SEARCH_PAGE_DELAY)
        else:
            # 普通搜索模式
            progress.update({"current_page": 0, "total_pages": max_pages,
                             "found": 0, "status": "searching"})

            for page_num in range(1, max_pages + 1):
                progress["current_page"] = page_num
                url = IEEE_SEARCH_URL.format(keyword=quote_plus(keyword), page=page_num)

                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_selector("xpl-results-list .List-results-items", timeout=20000)
                    await human_scroll(page)

                    papers = await self._parse_search_results(page)
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
        items = await page.query_selector_all("xpl-results-list .List-results-items")

        for item in items:
            try:
                paper = Paper(title="", source="IEEE")

                # 标题
                title_el = await item.query_selector("h3 a, .result-item-title a")
                if title_el:
                    paper.title = (await title_el.inner_text()).strip()
                    href = await title_el.get_attribute("href")
                    if href:
                        paper.url = IEEE_BASE_URL + href if href.startswith("/") else href
                        # 提取 arnumber
                        m = re.search(r'/document/(\d+)', href)
                        if m:
                            paper.arnumber = m.group(1)

                if not paper.title:
                    continue

                # 作者
                author_els = await item.query_selector_all(".author a, .col-12-lg-max a[href*='author']")
                for a_el in author_els:
                    name = (await a_el.inner_text()).strip()
                    if name:
                        paper.authors.append(Author(name=name))

                # 期刊名
                pub_el = await item.query_selector(".description a, .publisher-info-container a")
                if pub_el:
                    paper.journal = (await pub_el.inner_text()).strip()

                # 年份
                pub_info = await item.query_selector(".publisher-info-container, .description")
                if pub_info:
                    text = await pub_info.inner_text()
                    year_match = re.search(r'(20\d{2}|19\d{2})', text)
                    if year_match:
                        paper.year = year_match.group(1)

                # 部分摘要（搜索页可能有）
                abs_el = await item.query_selector(".js-displayer-content span, .result-item-abstract")
                if abs_el:
                    paper.abstract = (await abs_el.inner_text()).strip()

                papers.append(paper)
            except Exception:
                continue

        return papers

    async def _has_next_page(self, page: Page) -> bool:
        next_btn = await page.query_selector("button.next-btn:not([disabled]), .pagination-bar .next-btn:not([disabled])")
        return next_btn is not None

    async def fetch_detail(self, paper: Paper) -> Paper:
        if not paper.url:
            return paper

        page = await self.get_page()
        try:
            await page.goto(paper.url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_selector(".document-main-content, .abstract-text", timeout=15000)
            await human_scroll(page)

            # 完整摘要
            abs_el = await page.query_selector(".abstract-text div[xplmathjax], .abstract-text")
            if abs_el:
                paper.abstract = (await abs_el.inner_text()).strip()

            # DOI
            doi_el = await page.query_selector("a[href*='doi.org'], .stats-document-abstract-doi a")
            if doi_el:
                doi_text = await doi_el.get_attribute("href")
                if doi_text and "doi.org/" in doi_text:
                    paper.doi = doi_text.split("doi.org/")[-1]

            # 作者+单位：点击 Authors 标签
            authors_tab = await page.query_selector("button:has-text('Authors'), a:has-text('Authors')")
            if authors_tab:
                await authors_tab.click()
                await random_delay(1, 2)

                author_cards = await page.query_selector_all(".authors-accordion-container .accordion-body, .author-card")
                if author_cards:
                    new_authors = []
                    for card in author_cards:
                        name_el = await card.query_selector("a[href*='author'], .author-name, span")
                        aff_el = await card.query_selector(".author-affiliation, .affiliation, div:nth-child(2)")
                        name = (await name_el.inner_text()).strip() if name_el else ""
                        aff = (await aff_el.inner_text()).strip() if aff_el else ""
                        if name:
                            new_authors.append(Author(name=name, affiliation=aff))
                    if new_authors:
                        paper.authors = new_authors

            # PDF URL
            if paper.arnumber:
                paper.pdf_url = f"{IEEE_BASE_URL}/stampPDF/getPDF.jsp?arnumber={paper.arnumber}"

            await anti_scraping_pause(page, DETAIL_PAGE_DELAY)

        except Exception:
            pass

        return paper

    async def download_pdf(self, paper: Paper) -> bytes | None:
        if not paper.arnumber:
            return None

        page = await self.get_page()
        pdf_bytes = None

        # 拦截 PDF 响应
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
            """轮询等待 PDF 响应到达"""
            for _ in range(timeout * 2):
                if pdf_bytes is not None:
                    return True
                await asyncio.sleep(0.5)
            return False

        page.on("response", handle_response)

        try:
            # 尝试 stampPDF
            url = paper.pdf_url or f"{IEEE_BASE_URL}/stampPDF/getPDF.jsp?arnumber={paper.arnumber}"
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await wait_for_pdf(timeout=30)

            # 如果 stampPDF 没拿到，尝试 stamp
            if pdf_bytes is None:
                url2 = f"{IEEE_BASE_URL}/stamp/stamp.jsp?arnumber={paper.arnumber}"
                await page.goto(url2, wait_until="domcontentloaded", timeout=60000)
                await wait_for_pdf(timeout=20)

                # 可能需要点击 iframe 中的下载
                if pdf_bytes is None:
                    iframe = await page.query_selector("iframe#pdf")
                    if iframe:
                        src = await iframe.get_attribute("src")
                        if src:
                            await page.goto(src if src.startswith("http") else IEEE_BASE_URL + src,
                                            wait_until="domcontentloaded", timeout=60000)
                            await wait_for_pdf(timeout=20)

            await anti_scraping_pause(page, DOWNLOAD_DELAY)

        except Exception:
            pass
        finally:
            page.remove_listener("response", handle_response)

        return pdf_bytes
