<p align="center">
  <img src="assets/banner.svg" alt="TopGridScholar Banner" width="800" />
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT" /></a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776ab.svg" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Streamlit-1.30%2B-ff4b4b.svg" alt="Streamlit" />
  <img src="https://img.shields.io/badge/Playwright-1.40%2B-2ead33.svg" alt="Playwright" />
</p>

<p align="center">
  <a href="README.md">English</a> | <a href="README_zh.md">中文</a>
</p>

---

基于 Streamlit + Playwright 的学术论文搜索与批量下载工具，支持 **IEEE Xplore**、**Nature** 和 **Semantic Scholar**（CCF-A/B 期刊与会议）。通过浏览器自动化利用校园网权限下载 PDF 全文，并保留完整元数据。

## 功能特性

- **多源搜索** — IEEE Xplore、Nature、Semantic Scholar（CCF-A/B 期刊与会议）
- **批量下载** — 论文加入队列后自动下载，支持失败重试
- **校园网权限复用** — 使用持久化浏览器配置，登录一次即可长期使用
- **反爬策略** — 随机延迟、模拟人类滚动与鼠标移动
- **元数据导出** — 搜索结果可导出为 CSV（标题、作者、单位、DOI、摘要等）
- **断点续传** — 下载队列持久化，关闭应用后重启可继续

## 快速开始

```bash
pip install git+https://github.com/LuChuanfan/TopGridScholar.git
playwright install chromium
topgridscholar
```

## 环境要求

- **Python 3.10+**
- **校园网络**（校园 VPN 或校内网络）用于 IEEE/Nature 全文下载
- （可选）[Semantic Scholar API Key](https://www.semanticscholar.org/product/api) 用于 CCF-A/B 搜索

## 安装步骤

1. 安装：
   ```bash
   pip install git+https://github.com/LuChuanfan/TopGridScholar.git
   ```

2. 安装 Playwright 浏览器：
   ```bash
   playwright install chromium
   ```

3. （首次使用）设置浏览器登录：
   ```bash
   topgridscholar setup
   ```
   会打开一个 Chromium 窗口，请通过学校网络登录 IEEE Xplore / Nature，完成后关闭浏览器即可。登录状态会保存在本地。

## 配置

复制环境变量示例文件并编辑：

```bash
cp .env.example .env
```

| 变量 | 说明 | 是否必需 |
|---|---|---|
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API 密钥，用于 CCF-A/B 搜索 | 可选 |
| `PAPERDOWNLOADER_BASE_DIR` | 自定义数据存储目录（默认为当前工作目录） | 可选 |

## 使用方法

```bash
topgridscholar
```

Web 界面包含三个页面：

1. **搜索** — 输入关键词，选择数据源（IEEE / Nature / Semantic Scholar），执行搜索
2. **结果** — 浏览、筛选搜索结果，选择论文，导出 CSV
3. **下载** — 管理下载队列，查看进度，重试失败项

## 支持的数据源

| 数据源 | 搜索方式 | PDF 下载 | 需要登录 |
|---|---|---|---|
| IEEE Xplore | 关键词 / 按期刊 | stampPDF | 是（校园网） |
| Nature | 关键词 | 直接 PDF 链接 | 是（校园网） |
| Semantic Scholar | 关键词 + CCF 期刊筛选 | 仅 Open Access | 否（API Key 可选） |

## 注意事项

- **需要校园网权限** — IEEE 和 Nature 的 PDF 下载依赖校园网络或 VPN。没有权限时仍可搜索和查看元数据，但无法下载全文。
- **请遵守访问频率限制** — 工具内置了请求间隔延迟，请勿移除或缩短，否则可能触发反爬机制导致 IP 被封。
- **浏览器配置** — 登录 Cookie 保存在 `data/chrome_profile/`，请勿分享此目录。
- **数据目录** — 所有运行时数据（会话、下载、状态）存储在 `data/`，已被 `.gitignore` 排除。

## 常见问题

**Q：浏览器无法打开 / Playwright 在 Windows 上报错**
A：确保已运行 `playwright install chromium`。工具在 Windows 上会自动使用 `ProactorEventLoop` 以保证兼容性。

**Q：下载的 PDF 为空或文件很小**
A：通常是因为没有全文访问权限。请确认已连接校园网或 VPN。

**Q：Semantic Scholar 搜索无结果**
A：先尝试不加期刊筛选。如果出现 401/403 错误，请在 `.env` 文件中设置 `SEMANTIC_SCHOLAR_API_KEY`。

**Q：如何更改文件保存位置？**
A：在 `.env` 中设置 `PAPERDOWNLOADER_BASE_DIR` 为任意路径，工具会自动在该路径下创建 `data/` 子目录。

## 许可证

本项目基于 [MIT 许可证](LICENSE) 开源。
