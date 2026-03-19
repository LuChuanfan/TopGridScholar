from __future__ import annotations

import asyncio
import threading
from typing import Any, Callable, TypeVar
from concurrent.futures import Future
from pathlib import Path

T = TypeVar('T')


class AsyncBridge:
    """
    Streamlit(同步) ↔ Playwright(异步) 桥接器。
    在独立的后台线程中运行 asyncio 事件循环，
    管理 Playwright 浏览器上下文。
    """

    def __init__(self):
        self._loop: asyncio.AbstractEventLoop = None
        self._thread: threading.Thread = None
        self._started = False
        self._browser_context = None
        self._playwright = None

    def start(self):
        if self._started:
            return

        ready = threading.Event()

        def run_loop():
            # Windows 上必须用 ProactorEventLoop，否则 Playwright 无法启动子进程
            if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            ready.set()
            self._loop.run_forever()

        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
        ready.wait()
        self._started = True

    def submit(self, async_fn: Callable[..., Any], *args, **kwargs) -> Future:
        """
        提交一个 async 函数到后台事件循环执行（非阻塞）。
        关键：async_fn 的协程在后台线程中创建，不会触碰 Streamlit 线程的事件循环。
        """
        if not self._started:
            self.start()

        async def _wrapper():
            return await async_fn(*args, **kwargs)

        return asyncio.run_coroutine_threadsafe(_wrapper(), self._loop)

    def submit_sync(self, async_fn: Callable[..., Any], *args, **kwargs) -> Any:
        """提交并阻塞等待结果"""
        return self.submit(async_fn, *args, **kwargs).result()

    async def ensure_browser(self, chrome_profile_dir: Path, browser_args: list):
        """在后台事件循环中初始化浏览器（必须从后台线程调用）"""
        # 检测旧的浏览器是否已关闭：尝试真正创建一个页面
        if self._browser_context is not None:
            try:
                test_page = await self._browser_context.new_page()
                await test_page.close()
            except Exception:
                # 浏览器已失效，清理
                self._browser_context = None
                if self._playwright:
                    try:
                        await self._playwright.stop()
                    except Exception:
                        pass
                    self._playwright = None

        if self._browser_context is None:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser_context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(chrome_profile_dir),
                headless=False,
                args=browser_args,
                viewport={"width": 1280, "height": 800},
                locale="en-US",
            )
        return self._browser_context

    def stop(self):
        if self._loop and self._started:
            # 清理浏览器资源
            if self._browser_context or self._playwright:
                async def _cleanup():
                    if self._browser_context:
                        try:
                            await self._browser_context.close()
                        except Exception:
                            pass
                        self._browser_context = None
                    if self._playwright:
                        try:
                            await self._playwright.stop()
                        except Exception:
                            pass
                        self._playwright = None

                try:
                    future = asyncio.run_coroutine_threadsafe(_cleanup(), self._loop)
                    future.result(timeout=10)
                except Exception:
                    pass

            self._loop.call_soon_threadsafe(self._loop.stop)
            self._started = False
