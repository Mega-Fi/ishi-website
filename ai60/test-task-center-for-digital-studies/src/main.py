import asyncio
import logging
import sys

from . import db
from .scraper import fetch_top_articles

DB_PATH = "test_automation.db"
TOP_N = 10

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


async def run() -> None:
    articles = await fetch_top_articles(limit=TOP_N)

    saved = 0
    skipped = 0
    with db.connect(DB_PATH) as conn:
        db.init_schema(conn)
        for article in articles:
            if db.save_article(conn, article):
                saved += 1
            else:
                skipped += 1

    print(f"{saved} items saved, {skipped} items skipped due to existing state.")


def main() -> int:
    try:
        asyncio.run(run())
        return 0
    except KeyboardInterrupt:
        logger.warning("interrupted by user")
        return 130
    except Exception:
        logger.exception("unhandled error")
        return 1


if __name__ == "__main__":
    sys.exit(main())
