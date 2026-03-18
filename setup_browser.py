"""
首次使用：打开浏览器让用户手动登录 IEEE/Nature，保存 cookies 到持久化配置。
运行方式：python setup_browser.py
"""
import asyncio
from playwright.async_api import async_playwright
from config import CHROME_PROFILE_DIR, BROWSER_ARGS


async def main():
    CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  TopGridScholar - 浏览器登录设置")
    print("=" * 60)
    print()
    print("即将打开 Chromium 浏览器，请依次完成以下操作：")
    print("  1. 访问 ieeexplore.ieee.org 并通过学校网络登录")
    print("  2. 访问 nature.com 确认可以访问全文")
    print("  3. 完成后直接关闭浏览器窗口")
    print()
    print("浏览器配置将保存到:", CHROME_PROFILE_DIR)
    print()

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(CHROME_PROFILE_DIR),
            headless=False,
            args=BROWSER_ARGS,
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )

        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://ieeexplore.ieee.org/")

        print("浏览器已打开，请完成登录操作...")
        print("关闭浏览器窗口后，配置将自动保存。")

        # 等待用户关闭浏览器
        try:
            await context.pages[0].wait_for_event("close", timeout=0)
            # 等一下看是否所有页面都关了
            await asyncio.sleep(1)
        except Exception:
            pass

        try:
            await context.close()
        except Exception:
            pass

    print()
    print("浏览器配置已保存！现在可以运行 streamlit run app.py")


if __name__ == "__main__":
    if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
