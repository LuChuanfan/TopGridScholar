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

A Streamlit-based tool for searching and batch-downloading academic papers from **IEEE Xplore**, **Nature**, and **Semantic Scholar** (CCF-A/B venues). It uses browser automation to leverage your institutional access and downloads PDFs with full metadata.

## Features

- **Multi-source search** — IEEE Xplore, Nature, and Semantic Scholar (CCF-A/B journals & conferences)
- **Batch PDF download** — queue papers and download them automatically with retry support
- **Institutional access** — uses a persistent browser profile so your campus login session is preserved
- **Anti-scraping measures** — random delays, human-like scrolling, and mouse movement
- **Metadata export** — export search results to CSV (title, authors, affiliations, DOI, abstract, etc.)
- **Session persistence** — download queue survives restarts; interrupted downloads resume automatically

## Getting Started

**Prerequisites:** Python 3.10+, institutional network access (campus VPN or on-campus) for IEEE/Nature full-text downloads.

Run the following commands in CMD (Command Prompt) or PowerShell:

1. Install the package:
   ```bash
   pip install https://github.com/LuChuanfan/TopGridScholar/archive/refs/tags/v0.1.0.zip
   ```

2. Launch:
   ```bash
   topgridscholar
   ```
   Chromium browser will be installed automatically on first run, please wait patiently. After startup, the browser will open automatically. **(If the browser does not open automatically, visit http://localhost:8501 manually)**

3. (Optional) Set up browser login:
   ```bash
   topgridscholar setup
   ```
   If your campus network cannot directly download IEEE/Nature full-text PDFs, you need to run this step to log in via the browser. A Chromium window will open. Log in to IEEE Xplore / Nature through your institution, then close the browser. Your session cookies are saved locally. **If your campus network already grants access automatically (IP-based authentication), you can skip this step.**

## Configuration

All configuration is optional — the tool works out of the box with default settings.

| Variable | Description |
|---|---|
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API key. Only needed if you encounter 401/403 errors when using CCF-A/B search. Get one for free at [Semantic Scholar](https://www.semanticscholar.org/product/api) |
| `PAPERDOWNLOADER_BASE_DIR` | Custom data directory. By default, data is stored in `%USERPROFILE%\topgridscholar_data\` (under your C: drive user folder). Set this if you want to save papers to a different location (e.g. D: drive) |

**How to set environment variables on Windows (using `PAPERDOWNLOADER_BASE_DIR` as an example):**

1. Press `Win + I` to open Settings, search for "environment variables", click "Edit the system environment variables"
2. Click the "Environment Variables" button
3. Under "User variables", click "New"
4. Set variable name to `PAPERDOWNLOADER_BASE_DIR`, set value to your desired path (e.g. `D:\MyPapers`)
5. Click OK to save. Reopen your CMD window for the change to take effect

## Usage

The web UI has three pages:

1. **Search** — enter keywords, choose a source (IEEE / Nature / Semantic Scholar), and run the search
2. **Results** — browse, filter, and select papers; export metadata to CSV
3. **Download** — manage the download queue, monitor progress, retry failed items

## Supported Sources

| Source | Search | PDF Download | Requires Login |
|---|---|---|---|
| IEEE Xplore | Keyword / per-journal | Via stampPDF | Yes (institutional) |
| Nature | Keyword | Direct PDF link | Yes (institutional) |
| Semantic Scholar | Keyword + CCF venue filter | Open Access only | No (API key optional) |

## Important Notes

- **Institutional access required** — IEEE and Nature PDF downloads rely on your campus network or VPN. Without it, you can still search and view metadata, but PDFs may not be available.
- **Respect rate limits** — the tool includes built-in delays between requests. Do not remove or reduce them, as this may trigger anti-scraping protections and get your IP blocked.
- **Browser profile** — login cookies are stored in the `chrome_profile/` subdirectory of your data folder. Do not share this directory.
- **Data directory** — all runtime data (sessions, downloads, state) is stored in `%USERPROFILE%\topgridscholar_data\data\` by default. This can be customized via environment variable.

## FAQ

**Q: The browser doesn't open / Playwright fails on Windows.**
A: Chromium is installed automatically on first run. If automatic installation fails, you can try manually: `playwright install chromium`. On Windows, the tool automatically uses `ProactorEventLoop` for compatibility.

**Q: PDFs download as empty or very small files.**
A: This usually means you don't have access to the full text. Check that you're on your campus network or connected to your institution's VPN. It's also possible that your institution does not have a subscription to that particular journal.

**Q: Semantic Scholar search returns no results.**
A: Try without venue filters first. If you get a 401/403 error, set the `SEMANTIC_SCHOLAR_API_KEY` environment variable.

**Q: Can I change where files are saved?**
A: Set the `PAPERDOWNLOADER_BASE_DIR` environment variable to any path (e.g. `D:\MyPapers`). The tool will create `data/` subdirectories there. See the Configuration section above for how to set environment variables.

## License

This project is licensed under the [MIT License](LICENSE).
