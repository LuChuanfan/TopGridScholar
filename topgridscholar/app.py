import streamlit as st

st.set_page_config(
    page_title="TopGridScholar",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📚 TopGridScholar")
st.caption("学术论文搜索与下载工具 — IEEE Xplore · Nature · Semantic Scholar")

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🔍 搜索")
    st.write("输入关键词，从 IEEE Xplore 或 Nature 搜索论文。")
    st.page_link("pages/1_🔍_搜索.py", label="前往搜索", icon="🔍")

with col2:
    st.markdown("### 📋 结果")
    st.write("浏览、筛选搜索结果，选择要下载的论文。")
    st.page_link("pages/2_📋_结果.py", label="查看结果", icon="📋")

with col3:
    st.markdown("### 📥 下载")
    st.write("管理下载队列，查看下载进度。")
    st.page_link("pages/3_📥_下载.py", label="下载管理", icon="📥")

st.markdown("---")

with st.expander("首次使用说明"):
    st.markdown("""
1. 安装：`pip install https://github.com/LuChuanfan/TopGridScholar/archive/refs/tags/v0.1.0.zip`
2. 安装浏览器：`playwright install chromium`
3. 登录设置：`topgridscholar setup`（打开浏览器，手动登录学校账号）
4. 启动应用：`topgridscholar`
""")

with st.expander("注意事项"):
    st.markdown("""
- 搜索和下载均通过浏览器自动化完成，需要学校网络权限
- 为避免触发反爬机制，操作间会有随机延迟
- 下载队列支持断点续传，关闭应用后重启可继续
- 作者单位信息将在下载时从详情页获取
""")
