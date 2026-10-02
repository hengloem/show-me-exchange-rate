import requests
from bs4 import BeautifulSoup
from telegram import Bot
from datetime import datetime

# =========================
# CONFIGURATION
# =========================
BOT_TOKEN = "8762803453:AAFs5W3gjvhKinzfE9htO3M4ajVxprfB1qo"
CHAT_ID = "394846029"

NBC_URL = "https://www.nbc.gov.kh/english/economic_research/exchange_rate.php"

# currencies to display
WATCH_LIST = ["USD", "THB", "CNY", "EUR", "SGD", "VND"]

# =========================
# GET NBC DATA
# =========================
def get_exchange_rates():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(NBC_URL, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text("\n")

    official_rate = None
    rate_date = None

    for line in text.splitlines():
        line = line.strip()

        if "Official Exchange Rate" in line:
            official_rate = line.split(":")[-1].strip()

        if "Exchange Rate on" in line:
            rate_date = line.split(":")[-1].strip()

    tables = soup.find_all("table")

    rates = {}

    for table in tables:
        rows = table.find_all("tr")

        for row in rows:
            cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]

            if len(cols) >= 6:
                try:
                    currency_name = cols[0]
                    symbol = cols[1]
                    bid = cols[3]
                    ask = cols[4]
                    avg = cols[5]

                    code = symbol.split("/")[0]

                    rates[code] = {
                        "bid": bid,
                        "ask": ask,
                        "avg": avg,
                        "name": currency_name
                    }
                except:
                    pass

    return rate_date, official_rate, rates


# =========================
# BUILD MESSAGE
# =========================
def build_message():
    rate_date, official_rate, rates = get_exchange_rates()

    msg = []
    msg.append("🏦 NBC Daily Exchange Rate")
    msg.append(f"📅 {rate_date}")
    msg.append("")
    msg.append(f"💵 Official USD Rate: {official_rate}")
    msg.append("")

    for code in WATCH_LIST:
        if code == "USD":
            continue

        if code in rates:
            r = rates[code]

            msg.append(
                f"🔹 {code}: Avg {r['avg']} KHR"
            )

    msg.append("")
    msg.append(
        f"⏰ Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    return "\n".join(msg)


# =========================
# SEND TO TELEGRAM
# =========================
def send_telegram():
    bot = Bot(token=BOT_TOKEN)

    message = build_message()

    bot.send_message(
        chat_id=CHAT_ID,
        text=message
    )

    print("Message sent successfully")


if __name__ == "__main__":
    send_telegram()