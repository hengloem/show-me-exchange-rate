import os
import sys
import time
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

load_dotenv()

import requests
from bs4 import BeautifulSoup
from telegram import Bot

# =========================
# CONFIGURATION
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")

NBC_URL = "https://www.nbc.gov.kh/english/economic_research/exchange_rate.php"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 5  # seconds between retries

WATCH_LIST = ["USD", "THB", "CNY", "EUR", "SGD", "VND"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# =========================
# GET NBC DATA
# =========================
def fetch_with_retry(url: str) -> str:
    """Fetch a URL with retries and exponential backoff."""
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            logger.warning("Attempt %d/%d failed: %s", attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF * attempt)

    raise RuntimeError(f"Failed to fetch {url} after {MAX_RETRIES} attempts: {last_error}")


def parse_rates(html: str) -> tuple[str | None, str | None, dict]:
    """
    Parse the NBC page HTML and return:
        (rate_date, official_rate, rates_dict)

    rates_dict keys are currency codes, values are dicts with
    'bid', 'ask', 'avg', 'name'.
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n")

    official_rate = None
    rate_date = None

    lines = [l.strip() for l in text.splitlines()]

    for i, line in enumerate(lines):
        if rate_date is None and "Exchange Rate on" in line:
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j]:
                    rate_date = lines[j]
                    break

        if official_rate is None and "Official Exchange Rate" in line and "Cross Rate" not in line:
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j]:
                    official_rate = lines[j]
                    break

    rates: dict[str, dict[str, str]] = {}

    for table in soup.find_all("table"):
        rows = table.find_all("tr")

        for row in rows:
            cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]

            # Expect at least: name, symbol, _, bid, ask, avg
            if len(cols) < 6:
                continue

            currency_name = cols[0]
            symbol = cols[1]

            if not symbol:
                continue

            code = symbol.split("/")[0].strip().upper()

            if not code:
                continue

            rates[code] = {
                "bid": cols[3] if len(cols) > 3 else "",
                "ask": cols[4] if len(cols) > 4 else "",
                "avg": cols[5] if len(cols) > 5 else "",
                "name": currency_name,
            }

    return rate_date, official_rate, rates


def get_exchange_rates() -> tuple[str | None, str | None, dict]:
    """Fetch and parse the NBC exchange rate page."""
    html = fetch_with_retry(NBC_URL)
    return parse_rates(html)


# =========================
# BUILD MESSAGE
# =========================
def build_message() -> str:
    """Build the Telegram message from the scraped rates."""
    rate_date, official_rate, rates = get_exchange_rates()

    msg: list[str] = []
    today = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")

    msg.append("🏦 NBC Daily Exchange Rate")
    msg.append(f"📅 NBC Exchange Rate Date: {rate_date or 'N/A'}")

    if official_rate:
        msg.append(f"💵 Official USD Rate: {official_rate}")

    found_any = False
    for code in WATCH_LIST:
        if code == "USD":
            continue
        if code in rates:
            found_any = True
            r = rates[code]
            avg = r.get("avg") or "N/A"
            msg.append(f"🔹 {code}: Avg {avg} KHR")

    if not found_any:
        msg.append("⚠️ No watched currencies found in today's table.")

    msg.append(f"⏰ Updated: {today}")

    return "\n".join(msg)


# =========================
# SEND TO TELEGRAM
# =========================
def send_telegram() -> None:
    """Scrape rates and send them to Telegram."""
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("BOT_TOKEN and CHAT_ID environment variables are required.")
        sys.exit(1)

    bot = Bot(token=BOT_TOKEN)
    message = build_message()

    try:
        asyncio.run(bot.send_message(chat_id=CHAT_ID, text=message))
        logger.info("Message sent successfully.")
    except Exception as exc:
        logger.error("Failed to send Telegram message: %s", exc)
        raise


if __name__ == "__main__":
    send_telegram()
