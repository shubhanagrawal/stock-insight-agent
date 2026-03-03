#!/usr/bin/env python3
"""
main.py — Single-run entry point for the Stock Insight Agent pipeline.

Usage:
    python main.py                  # run one full pipeline cycle
    python scheduler.py             # run on a repeating schedule (every 15 min)
    streamlit run dashboard.py      # launch the interactive dashboard
"""

import logging
import sys
from config import FEEDS_TO_PROCESS
from worker import process_feed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s: %(message)s",
)


def main():
    logging.info("🚀 Stock Insight Agent — single pipeline run")
    logging.info(f"   Feeds configured: {list(FEEDS_TO_PROCESS.keys())}")

    if not FEEDS_TO_PROCESS:
        logging.error("No feeds configured in config.FEEDS_TO_PROCESS. Exiting.")
        sys.exit(1)

    for source_name, feed_config in FEEDS_TO_PROCESS.items():
        logging.info(f"  → Processing: {source_name} ({feed_config['url']})")
        process_feed(
            feed_url=feed_config["url"],
            source_weight=feed_config.get("weight", 1.0),
            article_limit=3,
        )

    logging.info("✅ Pipeline run complete. New insights saved to database.")


if __name__ == "__main__":
    main()
