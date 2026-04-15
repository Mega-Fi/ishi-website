import logging
from contextlib import AsyncExitStack
from urllib.parse import urljoin

from playwright.async_api import async_playwright

from .models import Article

logger = logging.getLogger(__name__)

HN_URL = "https://news.ycombinator.com/"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
NAV_TIMEOUT_MS = 30_000


def normalize_url(href: str, base: str = HN_URL) -> str:
    return urljoin(base, href.strip())


async def fetch_top_articles(limit: int = 10) -> list[Article]:
    logger.info("fetch_top_articles start", extra={"limit": limit})

    async with AsyncExitStack() as stack:
        pw = await stack.enter_async_context(async_playwright())
        browser = await pw.chromium.launch(headless=True)
        stack.push_async_callback(browser.close)

        context = await browser.new_context(user_agent=USER_AGENT)
        stack.push_async_callback(context.close)

        page = await context.new_page()
        stack.push_async_callback(page.close)

        await page.goto(HN_URL, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
        await page.wait_for_selector(".athing .titleline > a", timeout=NAV_TIMEOUT_MS)

        rows = page.locator(".athing").locator(".titleline > a")
        count = min(await rows.count(), limit)

        articles: list[Article] = []
        for i in range(count):
            anchor = rows.nth(i)
            title = (await anchor.inner_text()).strip()
            href = (await anchor.get_attribute("href")) or ""
            absolute_url = normalize_url(href)
            if title and absolute_url:
                articles.append(Article(title=title, url=absolute_url))

        logger.info("fetch_top_articles done", extra={"found": len(articles)})
        return articles

    # AsyncExitStack guarantees page, context, browser, and playwright
    # are torn down in reverse order on any exit path.
