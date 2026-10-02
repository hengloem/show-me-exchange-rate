# Show Me Exchange Rate

A Python script that scrapes the daily exchange rates from the National Bank of Cambodia (NBC) website and sends a formatted summary to a Telegram chat.

## What it does

- Fetches the official USD/KHR exchange rate and cross rates from the NBC website
- Extracts average rates for a configurable watch list of currencies (THB, CNY, EUR, SGD, VND)
- Sends a clean, formatted message to your Telegram chat with today's rates

## Sample output

```
🏦 NBC Daily Exchange Rate
📅 2026-10-02

💵 Official USD Rate: 4057

🔹 THB: Avg 121.50 KHR
🔹 CNY: Avg 608.00 KHR
🔹 EUR: Avg 4587.50 KHR
🔹 SGD: Avg 3188.50 KHR
🔹 VND: Avg 157.00 KHR

⏰ Updated: 2026-10-02 10:33:03
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create a Telegram bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts to create a bot
3. Copy the bot token BotFather gives you

### 3. Get your chat ID

1. Search for **@userinfobot** in Telegram and send it any message
2. It will reply with your chat ID (a number like `394846029`)

### 4. Configure environment variables

Create a `.env` file in the project root:

```
BOT_TOKEN=your_bot_token_here
CHAT_ID=your_chat_id_here
```

## Usage

```bash
python main.py
```

The script will fetch the latest rates from NBC and send them to your Telegram chat.

## Customization

Edit the `WATCH_LIST` in `main.py` to change which currencies appear in the message:

```python
WATCH_LIST = ["USD", "THB", "CNY", "EUR", "SGD", "VND"]
```

## Scheduling

To run this automatically every day, set up a cron job:

```bash
0 9 * * * cd /path/to/project && python main.py >> exchange_rate.log 2>&1
```

This runs the script at 9:00 AM daily.

## Data source

Exchange rates are scraped from the [National Bank of Cambodia](https://www.nbc.gov.kh/english/economic_research/exchange_rate.php) official website.

## License

Free to use and modify.
