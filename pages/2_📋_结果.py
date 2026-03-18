import streamlit as st
from pathlib import Path
from models import Paper
from managers.result_store import ResultStore
from managers.download_manager import DownloadManager
from config import DATA_DIR

st.set_page_config(page_title="结果 - PaperDownloader", page_icon="📋", layout="wide")
st.title("📋 搜索结果")

# 自定义样式
st.markdown("""
<style>
/* 论文列表区域：缩小每个 element-container 的间距 */
section.main div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] {
    margin-top: 0px !important;
    margin-bottom: 0px !important;
}
/* 缩小 columns 行的上下间距 */
section.main div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] {
    margin-top: 0px !important;
    margin-bottom: 0px !important;
    padding-top: 0px !important;
    padding-bottom: 0px !important;
}
/* 缩小 column 内部元素间距 */
div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {
    gap: 0rem !important;
}
div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] {
    margin-top: 0px !important;
    margin-bottom: 0px !important;
}
/* checkbox 紧凑 */
div[data-testid="stCheckbox"] {
    margin-top: 0px !important;
    margin-bottom: 0px !important;
    padding-top: 0px !important;
    padding-bottom: 0px !important;
}
/* markdown 段落紧凑 */
div[data-testid="stMarkdown"] p {
    margin-bottom: 0px !important;
}
</style>
""", unsafe_allow_html=True)

if "search_results" not in st.session_state:
    st.session_state.search_results = []

if "selected_indices" not in st.session_state:
    st.session_state.selected_indices = set()

# Shift+点击：记录上一次点击的行号
if "last_clicked" not in st.session_state:
    st.session_state.last_clicked = None

result_store = ResultStore()
download_manager = DownloadManager()

papers: list[Paper] = st.session_state.search_results

if not papers:
    # 没有当前搜索结果时，显示历史会话列表
    sessions = result_store.list_sessions()
    if sessions:
        st.markdown("### 历史搜索记录")
        st.caption(f"共 {len(sessions)} 条历史记录，点击加载后可继续操作")
        for i, s in enumerate(sessions[:20]):
            ts = s.get("timestamp", "")
            # 格式化时间
            if ts:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(ts)
                    ts_display = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    ts_display = ts[:16]
            else:
                ts_display = "未知时间"

            col_info, col_btn = st.columns([5, 1])
            with col_info:
                st.markdown(f"**{s['keyword']}** — {s['source']} — {s['count']}篇 — {ts_display}")
            with col_btn:
                if st.button("加载", key=f"load_hist_{i}", use_container_width=True):
                    kw, src, loaded_papers = result_store.load_session(Path(s["path"]))
                    st.session_state.search_results = loaded_papers
                    st.session_state.search_keyword = kw
                    st.session_state.search_sources = src.split("+") if "+" in src else [src]
                    st.session_state.selected_indices = set()
                    st.rerun()
    else:
        st.info("暂无搜索结果，请先前往「搜索」页进行搜索。")
    st.stop()

# === 筛选 ===
st.markdown("### 筛选")
col_f1, col_f2 = st.columns(2)

all_journals = sorted({p.journal for p in papers if p.journal})
all_years = sorted({p.year for p in papers if p.year}, reverse=True)

with col_f1:
    selected_journals = st.multiselect("按期刊筛选", all_journals, default=[])
with col_f2:
    selected_years = st.multiselect("按年份筛选", all_years, default=[])

filtered = papers
if selected_journals:
    filtered = [p for p in filtered if p.journal in selected_journals]
if selected_years:
    filtered = [p for p in filtered if p.year in selected_years]

# 建立 filtered 索引到 papers 原始索引的映射（避免 papers.index 在重复项时映射错误）
filtered_to_orig: list[int] = [
    i for i, p in enumerate(papers)
    if (not selected_journals or p.journal in selected_journals)
    and (not selected_years or p.year in selected_years)
]

# 同步 filtered 顺序为映射得到的顺序
filtered = [papers[i] for i in filtered_to_orig]

st.caption(f"显示 {len(filtered)} / {len(papers)} 篇")

# === 批量选择工具栏 ===
st.markdown("### 选择工具")

col_sel1, col_sel2, col_sel3, col_sel4 = st.columns([1, 1, 1, 1])

with col_sel1:
    if st.button("全选当前", use_container_width=True):
        st.session_state.selected_indices.update(filtered_to_orig)
        st.rerun()

with col_sel2:
    if st.button("取消全选", use_container_width=True):
        st.session_state.selected_indices = set()
        st.session_state.last_clicked = None
        st.rerun()

# A: 范围选择
with col_sel3:
    with st.popover("范围选择", use_container_width=True):
        range_start = st.number_input("起始行", min_value=1, max_value=max(len(filtered), 1), value=1, step=1)
        range_end = st.number_input("结束行", min_value=1, max_value=max(len(filtered), 1), value=min(10, len(filtered)), step=1)
        rc1, rc2 = st.columns(2)
        with rc1:
            if st.button("选中范围", use_container_width=True):
                for i in range(int(range_start) - 1, min(int(range_end), len(filtered))):
                    st.session_state.selected_indices.add(filtered_to_orig[i])
                st.rerun()
        with rc2:
            if st.button("取消范围", use_container_width=True):
                for i in range(int(range_start) - 1, min(int(range_end), len(filtered))):
                    st.session_state.selected_indices.discard(filtered_to_orig[i])
                st.rerun()

# C: 按期刊/年份快捷全选
with col_sel4:
    with st.popover("按条件选择", use_container_width=True):
        cond_tab1, cond_tab2 = st.tabs(["按期刊", "按年份"])
        with cond_tab1:
            if all_journals:
                pick_journal = st.selectbox("选择期刊", all_journals, key="pick_j")
                pj1, pj2 = st.columns(2)
                with pj1:
                    if st.button("选中该期刊", use_container_width=True):
                        for i, p in enumerate(filtered):
                            if p.journal == pick_journal:
                                st.session_state.selected_indices.add(filtered_to_orig[i])
                        st.rerun()
                with pj2:
                    if st.button("取消该期刊", use_container_width=True):
                        for i, p in enumerate(filtered):
                            if p.journal == pick_journal:
                                st.session_state.selected_indices.discard(filtered_to_orig[i])
                        st.rerun()
        with cond_tab2:
            if all_years:
                pick_year = st.selectbox("选择年份", all_years, key="pick_y")
                py1, py2 = st.columns(2)
                with py1:
                    if st.button("选中该年份", use_container_width=True):
                        for i, p in enumerate(filtered):
                            if p.year == pick_year:
                                st.session_state.selected_indices.add(filtered_to_orig[i])
                        st.rerun()
                with py2:
                    if st.button("取消该年份", use_container_width=True):
                        for i, p in enumerate(filtered):
                            if p.year == pick_year:
                                st.session_state.selected_indices.discard(filtered_to_orig[i])
                        st.rerun()

selected_count = len(st.session_state.selected_indices)
st.caption(f"已选中 {selected_count} 篇论文")

# === 论文列表（checkbox 模式） ===
st.markdown("---")
st.caption("提示: 先点一篇，再按住 Shift 点另一篇，可以范围选中中间所有论文。选中后可查看摘要（IEEE 和 Nature 来源的摘要需在下载时获取）")

for i, p in enumerate(filtered):
    orig_idx = filtered_to_orig[i]
    is_selected = orig_idx in st.session_state.selected_indices
    row_num = i + 1

    # 布局：checkbox | 标题 | 期刊 | 年份 | 来源 | 作者
    col_chk, col_title, col_journal, col_year, col_src, col_author = st.columns([0.3, 4, 1.8, 0.3, 0.5, 1.8])

    with col_chk:
        new_val = st.checkbox(
            f"{row_num}",
            value=is_selected,
            key=f"chk_{orig_idx}",
        )

    with col_title:
        st.markdown(f"**{p.title}**")

    with col_journal:
        st.markdown(p.journal)

    with col_year:
        st.markdown(p.year)

    with col_src:
        st.markdown(p.source)

    with col_author:
        authors_str = ", ".join(a.name for a in p.authors[:3])
        if len(p.authors) > 3:
            authors_str += "..."
        st.markdown(authors_str)

    # 选中后在该论文下方显示摘要
    if is_selected and p.abstract:
        st.markdown(f"📄 {p.abstract}")

    # 处理选中状态变化
    if new_val != is_selected:
        if new_val:
            st.session_state.selected_indices.add(orig_idx)
            st.session_state.last_clicked = i
        else:
            st.session_state.selected_indices.discard(orig_idx)
            # 取消选中时清除 last_clicked，避免下次选中时误触发范围选择
            st.session_state.last_clicked = None

# === 摘要预览（可展开） ===
st.markdown("---")
st.markdown("### 摘要预览")
st.caption("点击展开查看完整摘要和作者信息")

for i, p in enumerate(filtered):
    orig_idx = filtered_to_orig[i]
    prefix = "✅ " if orig_idx in st.session_state.selected_indices else ""
    with st.expander(f"{prefix}{p.title}"):
        st.write(f"**作者:** {', '.join(a.name for a in p.authors)}")
        st.write(f"**期刊:** {p.journal}  |  **年份:** {p.year}")
        if p.abstract:
            st.write(f"**摘要:** {p.abstract}")
        else:
            st.write("*摘要将在下载时从详情页获取*")
        if p.url:
            st.write(f"[查看原文]({p.url})")

# === 操作按钮 ===
st.markdown("---")
col_a1, col_a2, col_a3 = st.columns(3)

with col_a1:
    if st.button("📥 发送到下载队列", use_container_width=True, disabled=selected_count == 0):
        selected_papers = [papers[i] for i in sorted(st.session_state.selected_indices)]
        download_manager.add_papers(selected_papers)
        st.success(f"已添加 {len(selected_papers)} 篇论文到下载队列")

with col_a2:
    if st.button("📊 导出 CSV", use_container_width=True):
        export_papers = filtered if selected_count == 0 else [papers[i] for i in sorted(st.session_state.selected_indices)]
        csv_path = DATA_DIR / "export.csv"
        result_store.export_csv(export_papers, csv_path)
        st.success(f"已导出 {len(export_papers)} 篇论文到 {csv_path}")

        csv_data = csv_path.read_bytes()
        st.download_button("⬇️ 下载 CSV 文件", csv_data, "papers.csv", "text/csv")

with col_a3:
    st.info(f"💡 作者单位信息将在下载时从详情页获取")
