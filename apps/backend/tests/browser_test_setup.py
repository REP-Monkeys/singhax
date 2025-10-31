"""
Browser Testing Setup with Playwright

This module sets up browser testing capabilities for the application.
Run: pytest tests/browser_test_*.py --headed (to see browser)
     pytest tests/browser_test_*.py (headless)
"""

import pytest
import asyncio
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import os


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def browser():
    """Create a browser instance for all tests."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=os.getenv("PLAYWRIGHT_HEADED", "true").lower() == "false")
        yield browser
        await browser.close()


@pytest.fixture
async def context(browser: Browser):
    """Create a new browser context for each test."""
    context = await browser.new_context()
    yield context
    await context.close()


@pytest.fixture
async def page(context: BrowserContext):
    """Create a new page for each test."""
    page = await context.new_page()
    yield page
    await page.close()


@pytest.fixture
def frontend_url():
    """Get frontend URL from environment or use default."""
    return os.getenv("FRONTEND_URL", "http://localhost:3000")


@pytest.fixture
def backend_url():
    """Get backend URL from environment or use default."""
    return os.getenv("BACKEND_URL", "http://localhost:8000")


