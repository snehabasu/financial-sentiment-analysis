import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import os

# Make sure data directory exists
os.makedirs('data', exist_ok=True)

def get_stock_data(ticker, period="1mo", interval="1d"):
    """Fetch stock price data using yfinance"""
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period, interval=interval)
    return hist

def save_stock_data(ticker, data):
    """Save stock data to CSV"""
    filename = f"data/{ticker}_stock_data.csv"
    data.to_csv(filename)
    print(f"Saved stock data to {filename}")
    return filename

def get_yahoo_finance_news(ticker, max_articles=5):
    """Scrape recent news from Yahoo Finance for a specific stock"""
    url = f"https://finance.yahoo.com/quote/{ticker}/news"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        
        # Find news articles
        articles = soup.find_all('li', class_='js-stream-content')
        
        for i, article in enumerate(articles):
            if i >= max_articles:
                break
                
            title_element = article.find('h3')
            link_element = article.find('a', href=True)
            time_element = article.find('div', class_='C(#959595)')
            
            if title_element and link_element:
                title = title_element.text
                link = link_element['href']
                if not link.startswith('http'):
                    link = f"https://finance.yahoo.com{link}"
                
                # Extract time if available
                published_time = time_element.text if time_element else "N/A"
                
                news_items.append({
                    'ticker': ticker,
                    'title': title,
                    'url': link,
                    'published': published_time,
                    'source': 'Yahoo Finance',
                    'retrieved_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return news_items
    
    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")
        return []

def save_news_data(news_data):
    """Save news data to CSV"""
    if not news_data:
        print("No news data to save")
        return None
        
    df = pd.DataFrame(news_data)
    filename = f"data/financial_news_{datetime.now().strftime('%Y%m%d')}.csv"
    
    # Append to existing file if it exists
    if os.path.exists(filename):
        df.to_csv(filename, mode='a', header=False, index=False)
    else:
        df.to_csv(filename, index=False)
        
    print(f"Saved {len(news_data)} news items to {filename}")
    return filename

def main():
    # List of tickers to analyze
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']
    
    all_news = []
    
    # Get data for each ticker
    for ticker in tickers:
        print(f"Processing {ticker}...")
        
        # Get stock data
        stock_data = get_stock_data(ticker)
        save_stock_data(ticker, stock_data)
        
        # Get news
        news = get_yahoo_finance_news(ticker)
        all_news.extend(news)
        
        # Be nice to servers, don't hammer them
        time.sleep(2)
    
    # Save all collected news
    save_news_data(all_news)

if __name__ == "__main__":
    main()