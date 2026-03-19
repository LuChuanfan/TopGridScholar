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

## 开始使用

**环境要求：** Python 3.10+，校园网络（校园 VPN 或校内网络）用于 IEEE/Nature 全文下载。

以下命令在 CMD（命令提示符）或 PowerShell 中运行：

1. 安装：
   ```bash
   pip install https://github.com/LuChuanfan/TopGridScholar/archive/refs/tags/v0.1.0.zip
   ```

2. （首次使用）设置浏览器登录：
   ```bash
   topgridscholar setup
   ```
   首次运行时会自动安装 Chromium 浏览器。安装完成后会打开一个 Chromium 窗口，请通过学校网络登录 IEEE Xplore / Nature，完成后关闭浏览器即可。登录状态会保存在本地。**如果你的校园网已自动授权访问（IP 认证），则可跳过此步骤。**

3. 启动：
   ```bash
   topgridscholar
   ```

## 配置

以下配置均为可选，默认即可使用。

| 变量 | 说明 |
|---|---|
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API 密钥。仅在使用 CCF-A/B 搜索时遇到 401/403 错误才需要设置，可从 [Semantic Scholar](https://www.semanticscholar.org/product/api) 免费申请 |
| `PAPERDOWNLOADER_BASE_DIR` | 自定义数据存储目录。默认存储在 `%USERPROFILE%\topgridscholar_data\`（即 C 盘用户目录下）。如果想把论文下载到其他位置（如 D 盘），需要设置此变量 |

**Windows 设置环境变量方法（以 `PAPERDOWNLOADER_BASE_DIR` 为例）：**

1. 按 `Win + I` 打开设置，搜索"环境变量"，点击"编辑系统环境变量"
2. 点击"环境变量"按钮
3. 在"用户变量"中点击"新建"
4. 变量名填 `PAPERDOWNLOADER_BASE_DIR`，变量值填目标路径（如 `D:\我的论文`）
5. 确定保存后，重新打开 CMD 窗口即可生效

## 使用方法

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
- **浏览器配置** — 登录 Cookie 保存在数据目录的 `chrome_profile/` 下，请勿分享此目录。
- **数据目录** — 所有运行时数据（会话、下载、状态）默认存储在 `%USERPROFILE%\topgridscholar_data\data\`，可通过环境变量自定义。

## 常见问题

**Q：浏览器无法打开 / Playwright 在 Windows 上报错**
A：Chromium 浏览器会在首次运行时自动安装。如果自动安装失败，可以手动运行：`playwright install chromium`。工具在 Windows 上会自动使用 `ProactorEventLoop` 以保证兼容性。

**Q：下载的 PDF 为空或文件很小**
A：通常是因为没有全文访问权限。请确认已连接校园网或 VPN。也有可能是你的学校没有订阅该期刊的访问权限。

**Q：Semantic Scholar 搜索无结果**
A：先尝试不加期刊筛选。如果出现 401/403 错误，请设置环境变量 `SEMANTIC_SCHOLAR_API_KEY`。

**Q：如何更改文件保存位置？**
A：设置环境变量 `PAPERDOWNLOADER_BASE_DIR` 为任意路径（如 `D:\我的论文`），工具会自动在该路径下创建 `data/` 子目录。设置方法见上方「配置」部分。

## 许可证

本项目基于 [MIT 许可证](LICENSE) 开源。
