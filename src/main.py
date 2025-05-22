import os
import sys
import time
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import project modules
import data_collection
import sentiment
import visualization

def run_pipeline(tickers=None):
    """Run the complete sentiment analysis pipeline"""
    if tickers is None:
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META']
    
    print("=" * 50)
    print(f"Financial Sentiment Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Step 1: Collect data
    print("\n[1/3] Collecting financial data...")
    all_news = []
    
    for ticker in tickers:
        print(f"  Processing {ticker}...")
        
        # Get stock data
        stock_data = data_collection.get_stock_data(ticker)
        data_collection.save_stock_data(ticker, stock_data)
        
        # Get news

        news = data_collection.get_financial_news(ticker)
        all_news.extend(news)
        
        # Be nice to servers
        time.sleep(1)
    
    # Save all collected news
    news_file = data_collection.save_news_data(all_news)
    if not news_file:
        print("No news data collected. Exiting.")
        return
    
    # Step 2: Analyze sentiment
    print("\n[2/3] Analyzing sentiment...")
    output_file = news_file.replace('.csv', '_sentiment.csv')
    result_df, ticker_sentiment = sentiment.process_news_data(news_file, output_file)
    
    # Step 3: Create visualizations
    print("\n[3/3] Creating visualizations...")
    
    # Create output directory for visualizations
    viz_dir = os.path.join('data', 'visualizations')
    os.makedirs(viz_dir, exist_ok=True)
    
    # Plot overall sentiment by ticker
    viz_file = os.path.join(viz_dir, 'sentiment_by_ticker.png')
    visualization.plot_sentiment_by_ticker(ticker_sentiment, viz_file)
    
    # Plot sentiment vs price for each ticker
    for ticker in tickers:
        viz_file = os.path.join(viz_dir, f'{ticker}_sentiment_vs_price.png')
        visualization.plot_sentiment_vs_price(ticker, result_df, output_file=viz_file)
    
    print("\nAnalysis pipeline completed successfully!")

if __name__ == "__main__":
    # Get tickers from command line if provided
    tickers = sys.argv[1:] if len(sys.argv) > 1 else None
    run_pipeline(tickers)