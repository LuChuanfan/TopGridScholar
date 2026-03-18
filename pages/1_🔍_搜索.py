import time
import streamlit as st
from bridge import AsyncBridge
from config import CHROME_PROFILE_DIR, BROWSER_ARGS
from models import Paper
from scrapers.ieee import IEEEScraper
from scrapers.nature import NatureScraper
from scrapers.semantic_scholar import SemanticScholarScraper
from managers.result_store import ResultStore
from managers.keyword_history import KeywordHistory
from venues import VENUE_GROUPS

st.set_page_config(page_title="搜索 - PaperDownloader", page_icon="🔍", layout="wide")
st.title("🔍 论文搜索")

# === 初始化 session_state ===
if "bridge" not in st.session_state:
    st.session_state.bridge = AsyncBridge()
    st.session_state.bridge.start()

if "search_results" not in st.session_state:
    st.session_state.search_results = []

if "search_progress" not in st.session_state:
    st.session_state.search_progress = {}

if "search_future" not in st.session_state:
    st.session_state.search_future = None

if "search_keyword" not in st.session_state:
    st.session_state.search_keyword = ""

if "search_sources" not in st.session_state:
    st.session_state.search_sources = ["IEEE Trans"]

result_store = ResultStore()
keyword_history = KeywordHistory()
bridge: AsyncBridge = st.session_state.bridge


async def _do_search(keyword: str, selected_groups: list[str], max_pages: int, progress: dict):
    all_papers: list[Paper] = []

    # 收集各平台的搜索任务
    ieee_pub_titles: list[str] = []
    search_ieee = False
    search_nature = False
    ccf_venues: list[str] = []
    ccf_fullnames: list[str] = []
    search_ccf = False

    for group_name in selected_groups:
        group = VENUE_GROUPS.get(group_name)
        if not group:
            continue
        platform = group["platform"]
        if platform == "ieee":
            search_ieee = True
            ieee_pub_titles.extend(group.get("pub_titles", []))
        elif platform == "nature":
            search_nature = True
        elif platform == "semantic_scholar":
            search_ccf = True
            ccf_venues.extend(group["venues"])
            ccf_fullnames.extend(group.get("venue_fullnames", []))

    # IEEE Trans 搜索（需要浏览器）
    if search_ieee:
        context = await bridge.ensure_browser(CHROME_PROFILE_DIR, BROWSER_ARGS)
        progress["source"] = "IEEE Trans"
        scraper = IEEEScraper(context)
        async for page_papers in scraper.search(keyword, max_pages, progress,
                                                pub_titles=ieee_pub_titles or None):
            all_papers.extend(page_papers)
        await scraper.close_page()

    # CCF-A/B 搜索（Semantic Scholar API）
    if search_ccf:
        progress["source"] = "CCF-A/B"
        scraper = SemanticScholarScraper(venue_fullnames=ccf_fullnames or None)
        async for page_papers in scraper.search(keyword, max_pages, progress,
                                                venues=ccf_venues or None):
            all_papers.extend(page_papers)
        await scraper.close_page()

    # Nature 搜索（需要浏览器）
    if search_nature:
        context = await bridge.ensure_browser(CHROME_PROFILE_DIR, BROWSER_ARGS)
        progress["source"] = "Nature 系列"
        scraper = NatureScraper(context)
        async for page_papers in scraper.search(keyword, max_pages, progress):
            all_papers.extend(page_papers)
        await scraper.close_page()

    return all_papers


# === 关键词历史 ===
recent_keywords = keyword_history.get_recent(10)
if recent_keywords:
    st.caption("最近搜索：")
    cols = st.columns(min(len(recent_keywords), 5))
    for i, kw in enumerate(recent_keywords):
        col = cols[i % 5]
        with col:
            btn_col, del_col = st.columns([4, 1])
            with btn_col:
                if st.button(kw, key=f"hist_{i}", use_container_width=True):
                    st.session_state.search_keyword = kw
                    st.rerun()
            with del_col:
                if st.button("✕", key=f"del_{i}"):
                    keyword_history.delete(kw)
                    st.rerun()

# === 搜索表单 ===
with st.form("search_form"):
    keyword = st.text_input("关键词", value=st.session_state.search_keyword,
                            placeholder="例如: large language model agent")
    col1, col2 = st.columns(2)
    with col1:
        selected_sources = st.multiselect(
            "来源（可多选）",
            options=list(VENUE_GROUPS.keys()),
            default=st.session_state.search_sources,
        )
    with col2:
        max_pages = st.slider("最大页数", 1, 20, 3)

    submitted = st.form_submit_button("🔍 开始搜索", use_container_width=True)

if submitted and keyword.strip() and selected_sources:
    st.session_state.search_keyword = keyword.strip()
    st.session_state.search_sources = selected_sources
    st.session_state.search_results = []
    st.session_state.search_progress = {"status": "starting", "found": 0}

    # 记录关键词历史
    keyword_history.add(keyword.strip())

    future = bridge.submit(
        _do_search, keyword.strip(), selected_sources, max_pages, st.session_state.search_progress
    )
    st.session_state.search_future = future
    st.rerun()

# === 搜索进度 ===
if st.session_state.search_future is not None:
    future = st.session_state.search_future
    progress = st.session_state.search_progress

    if future.done():
        try:
            results = future.result()
            st.session_state.search_results = results
            st.success(f"搜索完成！共找到 {len(results)} 篇论文")
            # 自动保存搜索结果
            if results:
                source_label = "+".join(st.session_state.search_sources)
                result_store.save_session(
                    st.session_state.search_keyword,
                    source_label,
                    results,
                )
        except Exception as e:
            st.error(f"搜索出错: {e}")
        st.session_state.search_future = None
    else:
        status = progress.get("status", "")
        src = progress.get("source", "")
        current = progress.get("current_page", 0)
        total = progress.get("total_pages", 1)
        found = progress.get("found", 0)
        current_journal = progress.get("current_journal", "")

        # 显示底层状态（例如 API 认证失败/HTTP 错误/超时）
        if status and status not in ("starting", "searching", "completed"):
            if "认证失败" in status or "API 错误" in status:
                st.warning(status)
            else:
                st.caption(status)

        if current_journal:
            st.info(f"正在搜索 [{src}] — {current_journal} ({current}/{total}) — 已找到 {found} 篇")
        else:
            st.info(f"正在搜索 [{src}] — 第 {current}/{total} 页 — 已找到 {found} 篇")
        if total > 0:
            st.progress(current / total)

        time.sleep(2)
        st.rerun()

# === 保存/加载会话 ===
st.markdown("---")
col_save, col_load = st.columns(2)

with col_save:
    if st.session_state.search_results:
        if st.button("💾 保存搜索结果"):
            source_label = "+".join(st.session_state.search_sources)
            path = result_store.save_session(
                st.session_state.search_keyword,
                source_label,
                st.session_state.search_results,
            )
            st.success(f"已保存: {path.name}")

with col_load:
    sessions = result_store.list_sessions()
    if sessions:
        options = {s["filename"]: s for s in sessions}
        selected = st.selectbox(
            "加载历史会话",
            options.keys(),
            format_func=lambda x: f"{options[x]['keyword']} ({options[x]['source']}, {options[x]['count']}篇)",
        )
        if st.button("📂 加载"):
            from pathlib import Path
            kw, src, papers = result_store.load_session(Path(options[selected]["path"]))
            st.session_state.search_results = papers
            st.session_state.search_keyword = kw
            st.session_state.search_sources = src.split("+") if "+" in src else [src]
            st.success(f"已加载 {len(papers)} 篇论文")
            st.rerun()

# === 结果预览 ===
if st.session_state.search_results:
    st.markdown(f"### 搜索结果（{len(st.session_state.search_results)} 篇）")
    for i, p in enumerate(st.session_state.search_results[:10]):
        with st.expander(f"{i+1}. {p.title}"):
            st.write(f"**作者:** {', '.join(a.name for a in p.authors)}")
            st.write(f"**期刊:** {p.journal}  |  **年份:** {p.year}  |  **来源:** {p.source}")
            if p.abstract:
                st.write(f"**摘要:** {p.abstract[:300]}...")
            if p.url:
                st.write(f"[查看原文]({p.url})")

    if len(st.session_state.search_results) > 10:
        st.caption(f"仅显示前 10 条，共 {len(st.session_state.search_results)} 条。前往「结果」页查看全部。")
