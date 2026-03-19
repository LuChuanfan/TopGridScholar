from __future__ import annotations

import asyncio
import random
from playwright.async_api import Page


async def random_delay(min_sec: float, max_sec: float):
    """随机延迟"""
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)


async def human_scroll(page: Page, times: int = 0):
    """模拟人类滚动行为"""
    if times <= 0:
        times = random.randint(2, 5)
    for _ in range(times):
        distance = random.randint(200, 600)
        await page.mouse.wheel(0, distance)
        await asyncio.sleep(random.uniform(0.3, 1.0))


async def human_mouse_move(page: Page):
    """模拟随机鼠标移动"""
    viewport = page.viewport_size or {"width": 1280, "height": 800}
    for _ in range(random.randint(1, 3)):
        x = random.randint(100, viewport["width"] - 100)
        y = random.randint(100, viewport["height"] - 100)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.1, 0.4))


async def anti_scraping_pause(page: Page, delay_range: tuple[float, float]):
    """综合反爬：鼠标移动 + 滚动 + 随机延迟"""
    await human_mouse_move(page)
    await human_scroll(page, random.randint(1, 3))
    await random_delay(delay_range[0], delay_range[1])
