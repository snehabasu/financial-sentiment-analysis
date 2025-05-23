import yfinance as yf
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
import os
import sys

# API Configuration - Fix the import path issue
try:
    # Add the script's directory to Python path so it can find config.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    
    from config import MARKETAUX_API_KEY, FINNHUB_API_KEY, EODHD_API_KEY
    print("✓ Loaded API keys from config.py")
except ImportError:
    # Fallback if config.py doesn't exist or can't be imported
    MARKETAUX_API_KEY = os.getenv('MARKETAUX_API_KEY', 'demo')
    FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')
    EODHD_API_KEY = os.getenv('EODHD_API_KEY', '')
    print("Warning: config.py not found. Using environment variables for API keys.")

# Make sure data directory exists
os.makedirs('data', exist_ok=True)


class FastNewsCollector:
    """Collect financial news using multiple fast APIs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def get_finnhub_news(self, ticker, max_articles=10):
        """Get news from Finnhub API (very fast, good free tier)"""
        if not FINNHUB_API_KEY:
            return []
        
        url = f"https://finnhub.io/api/v1/company-news"
        params = {
            'symbol': ticker,
            'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
            'to': datetime.now().strftime('%Y-%m-%d'),
            'token': FINNHUB_API_KEY
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            news_items = []
            for i, item in enumerate(data[:max_articles]):
                news_items.append({
                    'ticker': ticker,
                    'title': item.get('headline', ''),
                    'summary': item.get('summary', ''),
                    'url': item.get('url', ''),
                    'published': datetime.fromtimestamp(item.get('datetime', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                    'source': item.get('source', 'Finnhub'),
                    'retrieved_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            print(f"✓ Finnhub: {len(news_items)} articles for {ticker}")
            return news_items
            
        except Exception as e:
            print(f"✗ Finnhub error for {ticker}: {e}")
            return []
    
    def get_marketaux_news(self, ticker, max_articles=10):
        """Get news from MarketAux API"""
        if not MARKETAUX_API_KEY or MARKETAUX_API_KEY == 'demo':
            return []
        
        url = f"https://api.marketaux.com/v1/news/all"
        params = {
            'symbols': ticker,
            'language': 'en',
            'limit': max_articles,
            'api_token': MARKETAUX_API_KEY
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            news_items = []
            if 'data' in data:
                for item in data['data']:
                    news_items.append({
                        'ticker': ticker,
                        'title': item.get('title', ''),
                        'summary': item.get('description', ''),
                        'url': item.get('url', ''),
                        'published': item.get('published_at', ''),
                        'source': item.get('source', 'MarketAux'),
                        'retrieved_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            print(f"✓ MarketAux: {len(news_items)} articles for {ticker}")
            return news_items
            
        except Exception as e:
            print(f"✗ MarketAux error for {ticker}: {e}")
            return []
    
    def get_eodhd_news(self, ticker, max_articles=10):
        """Get news from EODHD API (includes sentiment data!)"""
        if not EODHD_API_KEY:
            return []
        
        url = f"https://eodhd.com/api/news"
        params = {
            's': f"{ticker}.US",
            'api_token': EODHD_API_KEY,
            'limit': max_articles,
            'fmt': 'json'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            news_items = []
            for item in data:
                news_items.append({
                    'ticker': ticker,
                    'title': item.get('title', ''),
                    'summary': item.get('content', ''),
                    'url': item.get('link', ''),
                    'published': item.get('date', ''),
                    'source': 'EODHD',
                    'retrieved_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            print(f"✓ EODHD: {len(news_items)} articles for {ticker}")
            return news_items
            
        except Exception as e:
            print(f"✗ EODHD error for {ticker}: {e}")
            return []
    
    def get_alpha_vantage_news(self, ticker, max_articles=10):
        """Get news from Alpha Vantage (free tier available)"""
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not api_key:
            return []
        
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': ticker,
            'apikey': api_key,
            'limit': max_articles
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            news_items = []
            if 'feed' in data:
                for item in data['feed']:
                    news_items.append({
                        'ticker': ticker,
                        'title': item.get('title', ''),
                        'summary': item.get('summary', ''),
                        'url': item.get('url', ''),
                        'published': item.get('time_published', ''),
                        'source': item.get('source', 'Alpha Vantage'),
                        'retrieved_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        # Alpha Vantage includes sentiment!
                        'overall_sentiment_score': item.get('overall_sentiment_score', 0),
                        'overall_sentiment_label': item.get('overall_sentiment_label', 'Neutral')
                    })
            
            print(f"✓ Alpha Vantage: {len(news_items)} articles for {ticker}")
            return news_items
            
        except Exception as e:
            print(f"✗ Alpha Vantage error for {ticker}: {e}")
            return []


def get_stock_data(ticker, period="1mo", interval="1d"):
    """Fetch stock price data using yfinance (this is already fast)"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        return hist
    except Exception as e:
        print(f"Error fetching stock data for {ticker}: {e}")
        return pd.DataFrame()


def save_stock_data(ticker, data):
    """Save stock data to CSV"""
    if data.empty:
        print(f"No stock data to save for {ticker}")
        return None
    
    filename = f"data/{ticker}_stock_data.csv"
    data.to_csv(filename)
    print(f"✓ Saved stock data to {filename}")
    return filename


def get_financial_news_fast(ticker, max_articles=10):
    """Get news using fast APIs with fallback"""
    collector = FastNewsCollector()
    all_news = []
    
    # Try APIs in order of speed/reliability
    apis_to_try = [
        ('Finnhub', collector.get_finnhub_news),
        ('Alpha Vantage', collector.get_alpha_vantage_news),
        ('MarketAux', collector.get_marketaux_news),
        ('EODHD', collector.get_eodhd_news),
    ]
    
    for api_name, api_func in apis_to_try:
        try:
            news = api_func(ticker, max_articles)
            if news:
                all_news.extend(news)
                if len(all_news) >= max_articles:
                    break
        except Exception as e:
            print(f"Error with {api_name} for {ticker}: {e}")
            continue
    
    # Remove duplicates based on title
    seen_titles = set()
    unique_news = []
    for item in all_news:
        title = item.get('title', '').lower().strip()
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_news.append(item)
    
    return unique_news[:max_articles]


def save_news_data(news_data):
    """Save news data to CSV"""
    if not news_data:
        print("No news data to save")
        return None
    
    df = pd.DataFrame(news_data)
    filename = f"data/financial_news_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    # Append to existing file if it exists from today
    today_file = f"data/financial_news_{datetime.now().strftime('%Y%m%d')}.csv"
    if os.path.exists(today_file):
        df.to_csv(today_file, mode='a', header=False, index=False)
        print(f"✓ Appended {len(news_data)} news items to {today_file}")
        return today_file
    else:
        df.to_csv(filename, index=False)
        print(f"✓ Saved {len(news_data)} news items to {filename}")
        return filename


def setup_api_keys():
    """Helper function to set up API keys"""
    print("🔧 API Setup Guide:")
    print("For fastest performance, get these free API keys:")
    print("")
    print("1. Finnhub (Best free tier): https://finnhub.io/register")
    print("   - 60 calls/minute free")
    print("   - Set: export FINNHUB_API_KEY='your_key'")
    print("")
    print("2. Alpha Vantage (Includes sentiment): https://www.alphavantage.co/support/#api-key")
    print("   - 25 calls/day free, includes sentiment scores")
    print("   - Set: export ALPHA_VANTAGE_API_KEY='your_key'")
    print("")
    print("3. MarketAux (Good coverage): https://www.marketaux.com/account/dashboard")
    print("   - 100 calls/month free")
    print("   - Set: export MARKETAUX_API_KEY='your_key'")
    print("")
    print("4. EODHD (Financial focus): https://eodhd.com/register")
    print("   - Set: export EODHD_API_KEY='your_key'")
    print("")


def main():
    """Main data collection function"""
    # Default tickers - you can modify this list
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META']
    
    print("🚀 Fast Financial Data Collection")
    print("=" * 50)
    
    # Check if any API keys are configured
    has_api_keys = any([FINNHUB_API_KEY, MARKETAUX_API_KEY, EODHD_API_KEY, 
                       os.getenv('ALPHA_VANTAGE_API_KEY')])
    
    if not has_api_keys:
        print("⚠️  No API keys detected!")
        setup_api_keys()
        print("\nContinuing with demo keys (limited data)...\n")
    
    all_news = []
    
    # Collect data for each ticker
    for i, ticker in enumerate(tickers, 1):
        print(f"\n[{i}/{len(tickers)}] Processing {ticker}...")
        
        # Get stock data (fast)
        stock_data = get_stock_data(ticker)
        save_stock_data(ticker, stock_data)
        
        # Get news (fast APIs)
        news = get_financial_news_fast(ticker, max_articles=5)
        if news:
            all_news.extend(news)
            print(f"✓ {len(news)} news articles collected for {ticker}")
        else:
            print(f"✗ No news found for {ticker}")
        
        # Small delay to be respectful to APIs
        if i < len(tickers):
            time.sleep(0.5)
    
    # Save all collected news
    if all_news:
        save_news_data(all_news)
        print(f"\n🎉 Collection complete! Total: {len(all_news)} news articles")
    else:
        print("\n❌ No news collected. Check your API keys.")


if __name__ == "__main__":
    main()