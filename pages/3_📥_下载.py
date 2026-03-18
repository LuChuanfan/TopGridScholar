import time
import streamlit as st
from bridge import AsyncBridge
from config import CHROME_PROFILE_DIR, BROWSER_ARGS, DOWNLOADS_DIR
from models import DownloadStatus
from managers.download_manager import DownloadManager

st.set_page_config(page_title="下载 - PaperDownloader", page_icon="📥", layout="wide")
st.title("📥 下载管理")

# === 初始化 ===
if "bridge" not in st.session_state:
    st.session_state.bridge = AsyncBridge()
    st.session_state.bridge.start()

if "download_progress" not in st.session_state:
    st.session_state.download_progress = {}

if "download_future" not in st.session_state:
    st.session_state.download_future = None

if "download_manager" not in st.session_state:
    st.session_state.download_manager = DownloadManager()

dm: DownloadManager = st.session_state.download_manager

is_download_running = (
    st.session_state.download_future is not None
    and not st.session_state.download_future.done()
)
if not is_download_running:
    dm.load_state()

bridge: AsyncBridge = st.session_state.bridge


async def _do_download(progress: dict):
    context = await bridge.ensure_browser(CHROME_PROFILE_DIR, BROWSER_ARGS)
    await dm.run_downloads(context, progress)


# === 显示下载存储目录 ===
st.caption(f"下载目录: {DOWNLOADS_DIR}")

# === 统计 ===
stats = dm.stats
col_s1, col_s2, col_s3, col_s4 = st.columns(4)
col_s1.metric("总计", stats["total"])
col_s2.metric("已完成", stats["completed"])
col_s3.metric("失败", stats["failed"])
col_s4.metric("待下载", stats["pending"] + stats["in_progress"])

if stats["total"] > 0:
    completed_ratio = stats["completed"] / stats["total"]
    st.progress(completed_ratio, text=f"总体进度: {stats['completed']}/{stats['total']}")

# === 控制按钮 ===
st.markdown("---")
is_running = is_download_running
is_paused = dm._paused

col_b1, col_b2, col_b3, col_b4 = st.columns(4)

with col_b1:
    if is_running and is_paused:
        if st.button("▶️ 继续下载", use_container_width=True):
            dm.resume()
            st.rerun()
    else:
        if st.button("▶️ 开始下载", use_container_width=True,
                     disabled=is_running or stats["pending"] == 0):
            st.session_state.download_progress = {
                "status": "starting", "current_paper": "", "current_status": ""
            }
            future = bridge.submit(_do_download, st.session_state.download_progress)
            st.session_state.download_future = future
            st.rerun()

with col_b2:
    if st.button("⏸️ 暂停", use_container_width=True,
                 disabled=not is_running or is_paused):
        dm.pause()
        st.rerun()

with col_b3:
    if st.button("🔄 重试失败", use_container_width=True,
                 disabled=is_running or stats["failed"] == 0):
        dm.retry_all_failed()
        st.success("已重置所有失败任务")
        st.rerun()

with col_b4:
    if st.button("🗑️ 清空已完成", use_container_width=True,
                 disabled=is_running or stats["completed"] == 0):
        dm.clear_completed()
        st.success("已清空已完成任务")
        st.rerun()

# === 下载进度 ===
if st.session_state.download_future is not None:
    future = st.session_state.download_future
    progress = st.session_state.download_progress

    if future.done():
        try:
            future.result()
            st.success("下载队列执行完毕")
        except Exception as e:
            st.error(f"下载出错: {e}")
        st.session_state.download_future = None
        dm.load_state()
    else:
        if is_paused:
            st.warning("下载已暂停，点击「继续下载」恢复")
        else:
            current_paper = progress.get("current_paper", "")
            current_status = progress.get("current_status", "")
            if current_paper:
                st.info(f"正在处理: {current_paper[:60]}... — {current_status}")

        time.sleep(2)
        st.rerun()

# === 下载队列列表 ===
st.markdown("---")
st.markdown("### 下载队列")

if not dm.tasks:
    st.info("下载队列为空。请在「结果」页选择论文并发送到下载队列。")
else:
    STATUS_ICONS = {
        DownloadStatus.PENDING: "⏳",
        DownloadStatus.FETCHING_DETAIL: "🔍",
        DownloadStatus.DOWNLOADING: "⬇️",
        DownloadStatus.COMPLETED: "✅",
        DownloadStatus.FAILED: "❌",
        DownloadStatus.PAUSED: "⏸️",
    }

    # 分页显示，避免任务太多导致页面卡顿
    PAGE_SIZE = 100
    total_tasks = len(dm.tasks)
    total_pages = max(1, (total_tasks + PAGE_SIZE - 1) // PAGE_SIZE)

    if "task_page" not in st.session_state:
        st.session_state.task_page = 1
    # 确保页码有效
    st.session_state.task_page = min(st.session_state.task_page, total_pages)

    # 筛选按钮
    col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
    with col_filter1:
        show_filter = st.selectbox("筛选状态", ["全部", "待下载", "已完成", "失败"],
                                   key="task_filter")

    # 按状态筛选
    if show_filter == "待下载":
        display_tasks = [(i, t) for i, t in enumerate(dm.tasks) if t.status == DownloadStatus.PENDING]
    elif show_filter == "已完成":
        display_tasks = [(i, t) for i, t in enumerate(dm.tasks) if t.status == DownloadStatus.COMPLETED]
    elif show_filter == "失败":
        display_tasks = [(i, t) for i, t in enumerate(dm.tasks) if t.status == DownloadStatus.FAILED]
    else:
        display_tasks = list(enumerate(dm.tasks))

    st.caption(f"共 {len(display_tasks)} 条（总 {total_tasks} 条）")

    # 分页
    total_display = len(display_tasks)
    total_pages = max(1, (total_display + PAGE_SIZE - 1) // PAGE_SIZE)
    st.session_state.task_page = min(st.session_state.task_page, total_pages)
    page_start = (st.session_state.task_page - 1) * PAGE_SIZE
    page_end = min(page_start + PAGE_SIZE, total_display)
    page_tasks = display_tasks[page_start:page_end]

    to_delete = None

    for orig_idx, task in page_tasks:
        icon = STATUS_ICONS.get(task.status, "❓")
        title = task.paper.title[:70]
        status_text = task.status.value

        col_t1, col_t2, col_t3 = st.columns([5, 1, 0.5])
        with col_t1:
            st.write(f"{icon} **{title}**")
            if task.error_message:
                st.caption(f"⚠️ {task.error_message}")
            if task.file_path:
                st.caption(f"📁 {task.file_path}")
        with col_t2:
            st.caption(status_text)
        with col_t3:
            if not is_running:
                if st.button("✕", key=f"del_task_{orig_idx}"):
                    to_delete = orig_idx

    if to_delete is not None:
        dm.remove_task(to_delete)
        st.rerun()

    # 分页导航
    if total_pages > 1:
        col_prev, col_page_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("上一页", disabled=st.session_state.task_page <= 1):
                st.session_state.task_page -= 1
                st.rerun()
        with col_page_info:
            st.caption(f"第 {st.session_state.task_page} / {total_pages} 页")
        with col_next:
            if st.button("下一页", disabled=st.session_state.task_page >= total_pages):
                st.session_state.task_page += 1
                st.rerun()
