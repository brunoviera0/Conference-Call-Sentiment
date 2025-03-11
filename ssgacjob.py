from google.cloud import datastore
import yfinance as yf
import time
from datetime import datetime

# Initialize Google Cloud Datastore client
client = datastore.Client()

# Define Datastore Kind
kind = "SSGADailyPrices"

# List of tickers
tickers = [
    "ORCL", "GOOGL", "META", "MSFT", "AMZN", 
    "NOW", "CRM", "ADBE", "APP", "PLTR", 
    "INTU", "TRI"
]

# Get today's date
today_str = datetime.utcnow().strftime('%Y-%m-%d')

# Function to fetch and upload today's stock data
def fetch_and_store_daily_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")

        if data.empty:
            print(f"No data found for {ticker} today ({today_str})")
            return None

        # Extract today's row
        latest_row = data.iloc[-1]
        open_price = float(latest_row["Open"])
        high_price = float(latest_row["High"])
        low_price = float(latest_row["Low"])
        close_price = float(latest_row["Close"])
        volume = int(latest_row["Volume"])
        dividends = float(latest_row["Dividends"])
        stock_splits = float(latest_row["Stock Splits"])

        # Create unique key: "AAPL_2025-03-08"
        entity_key = client.key(kind, f"{ticker}_{today_str}")

        # Create entity
        entity = datastore.Entity(entity_key)
        entity.update({
            "Ticker": ticker,
            "Date": today_str,
            "Open": open_price,
            "High": high_price,
            "Low": low_price,
            "Close": close_price,
            "Volume": volume,
            "Dividends": dividends,
            "Stock Splits": stock_splits
        })

        # Save entity in Datastore
        client.put(entity)
        print(f"Stored {ticker} stock data for {today_str} in Datastore.")

    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")

# Loop through all stocks and store daily data
for ticker in tickers:
    fetch_and_store_daily_stock_data(ticker)
    time.sleep(2)  # Prevent API rate limiting

print("Daily stock data upload complete!")
