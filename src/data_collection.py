import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import os

try:
    from config import MARKETAUX_API_KEY
except ImportError:
    # Fallback if config.py doesn't exist
    MARKETAUX_API_KEY = "demo"
    print("Warning: config.py not found. Using demo API key for MarketAux.")

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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        
        # Try multiple potential selectors for Yahoo Finance
        articles = soup.find_all('li', class_='js-stream-content')
        
        if not articles:
            # Try alternative selector (Yahoo Finance layout may change)
            articles = soup.find_all('div', {'class': 'Ov(h)'})
        
        if not articles:
            # Another common pattern
            articles = soup.find_all('h3', {'class': 'Mb(5px)'})
            if articles:
                # Convert h3 elements to their parent article elements
                articles = [h.parent for h in articles if h.parent]
        
        if articles:
            print(f"Found {len(articles)} news articles for {ticker} on Yahoo Finance")
        else:
            print(f"Could not find news articles for {ticker} on Yahoo Finance")
            return []
        
        for i, article in enumerate(articles):
            if i >= max_articles:
                break
                
            # Try different ways to extract title and link
            title_element = article.find('h3') or article.find('a', {'data-test': 'title'})
            link_element = article.find('a', href=True)
            
            # Try different time selectors
            time_element = (
                article.find('div', class_='C(#959595)') or 
                article.find('div', {'data-test': 'pub-date'}) or
                article.find('span', {'data-test': 'pub-date'})
            )
            
            if title_element and link_element:
                title = title_element.get_text(strip=True)
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
        print(f"Error fetching news for {ticker} from Yahoo Finance: {e}")
        return []
    

def get_marketaux_news(ticker, api_key=MARKETAUX_API_KEY, max_articles=5):
    """Get news from MarketAux API (free tier available)"""
    url = f"https://api.marketaux.com/v1/news/all?symbols={ticker}&language=en&api_token={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        news_items = []
        if 'data' in data:
            for i, item in enumerate(data['data']):
                if i >= max_articles:
                    break
                    
                news_items.append({
                    'ticker': ticker,
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'published': item.get('published_at', ''),
                    'source': item.get('source', 'MarketAux'),
                    'retrieved_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
        return news_items
    
    except Exception as e:
        print(f"Error fetching MarketAux news for {ticker}: {e}")
        return []   
    
def get_financial_news(ticker, max_articles=5):
    """Get news using multiple real news sources with fallback"""
    # Try Yahoo Finance first
    print(f"Trying Yahoo Finance for {ticker}...")
    news = get_yahoo_finance_news(ticker, max_articles)
    
    # If Yahoo Finance fails or returns no news, try MarketAux
    if not news:
        print(f"Yahoo Finance returned no results for {ticker}. Trying MarketAux...")
        news = get_marketaux_news(ticker, max_articles=max_articles)
    
    if news:
        print(f"Successfully retrieved {len(news)} news items for {ticker}")
    else:
        print(f"No news found for {ticker} from any source.")
    
    return news

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
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META']
    
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