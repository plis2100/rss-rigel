from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests
from dateutil import parser as date_parser
from feedgen.feed import FeedGenerator


SOURCE_RSS = "https://www.rigel.com/investors/news-events/press-releases/rss"
NEWS_PAGE = "https://www.rigel.com/investors/news-events/press-releases"
OUTPUT_FILE = Path("docs/feed.xml")

GITHUB_RSS = (
    "https://raw.githubusercontent.com/"
    "plis2100/rss-rigel/main/docs/feed.xml"
)
