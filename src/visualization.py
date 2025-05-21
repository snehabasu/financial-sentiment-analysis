import pandas as pd
import matplotlib.pyplot as plt
import os
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np

def plot_sentiment_by_ticker(sentiment_data, output_file=None):
    """Plot average sentiment by ticker"""
    # If sentiment_data is a DataFrame with ticker and sentiment_score
    if isinstance(sentiment_data, pd.DataFrame) and 'ticker' in sentiment_data.columns:
        ticker_sentiment = sentiment_data.groupby('ticker').agg({
            'sentiment_score': 'mean',
            'ticker': 'count'
        }).rename(columns={'ticker': 'article_count'})
    else:
        # Assume it's already aggregated
        ticker_sentiment = sentiment_data
    
    # Sort by sentiment score
    ticker_sentiment = ticker_sentiment.sort_values('sentiment_score')
    
    # Create figure with two subplots sharing x-axis
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    
    # Plot sentiment scores
    bars = ax1.bar(ticker_sentiment.index, ticker_sentiment['sentiment_score'], color='skyblue')
    
    # Color bars based on sentiment (red for negative, green for positive)
    for i, bar in enumerate(bars):
        if ticker_sentiment['sentiment_score'].iloc[i] < 0:
            bar.set_color('salmon')
        else:
            bar.set_color('lightgreen')
    
    # Add horizontal line at y=0
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # Add labels and title
    ax1.set_ylabel('Sentiment Score (-1 to 1)')
    ax1.set_title('Average Sentiment by Ticker')
    
    # Add article counts in the second subplot
    ax2.bar(ticker_sentiment.index, ticker_sentiment['article_count'], color='gray', alpha=0.7)
    ax2.set_ylabel('Article Count')
    ax2.set_xlabel('Ticker')
    
    # Rotate x-axis labels
    plt.xticks(rotation=45)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save if output file is provided
    if output_file:
        plt.savefig(output_file)
        print(f"Saved visualization to {output_file}")
    
    plt.show()

def plot_sentiment_vs_price(ticker, sentiment_data, price_data=None, days=7, output_file=None):
    """Plot sentiment vs price for a specific ticker"""
    # Filter sentiment data for the ticker
    ticker_sentiment = sentiment_data[sentiment_data['ticker'] == ticker]
    
    if ticker_sentiment.empty:
        print(f"No sentiment data available for {ticker}")
        return
    
    # Convert published date to datetime
    try:
        ticker_sentiment['published_date'] = pd.to_datetime(ticker_sentiment['published'])
    except:
        # If we can't parse the dates, just use retrieved_date
        ticker_sentiment['published_date'] = pd.to_datetime(ticker_sentiment['retrieved_date'])
    
    # Sort by date
    ticker_sentiment = ticker_sentiment.sort_values('published_date')
    
    # Get stock price data if not provided
    if price_data is None:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        price_data = yf.download(ticker, start=start_date, end=end_date)
    
    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot stock price
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Stock Price ($)', color='tab:blue')
    ax1.plot(price_data.index, price_data['Close'], color='tab:blue', label='Stock Price')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    
    # Create second y-axis
    ax2 = ax1.twinx()
    ax2.set_ylabel('Sentiment Score', color='tab:red')
    
    # Plot sentiment as scatter points
    ax2.scatter(ticker_sentiment['published_date'], ticker_sentiment['sentiment_score'], 
                color='tab:red', alpha=0.7, label='News Sentiment')
    
    # Add trend line if we have enough points
    if len(ticker_sentiment) > 1:
        try:
            # Convert dates to numbers for linear regression
            x = np.array([(d - pd.Timestamp("1970-01-01")) // pd.Timedelta('1D') 
                         for d in ticker_sentiment['published_date']])
            y = ticker_sentiment['sentiment_score'].values
            
            # Calculate trend line
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            
            # Plot trend line
            x_line = np.array([min(x), max(x)])
            ax2.plot(pd.to_datetime(x_line, unit='D', origin='unix'), p(x_line), 
                     "r--", alpha=0.7, label='Sentiment Trend')
        except Exception as e:
            print(f"Could not calculate trend line: {e}")
    
    ax2.tick_params(axis='y', labelcolor='tab:red')
    
    # Add title and legend
    plt.title(f'{ticker}: Stock Price vs. News Sentiment')
    
    # Create combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # Format x-axis date labels
    fig.autofmt_xdate()
    
    # Adjust layout
    plt.tight_layout()
    
    # Save if output file is provided
    if output_file:
        plt.savefig(output_file)
        print(f"Saved visualization to {output_file}")
    
    plt.show()

def main():
    # Find the most recent sentiment analysis file
    data_dir = 'data'
    sentiment_files = [f for f in os.listdir(data_dir) 
                       if f.endswith('_sentiment.csv')]
    
    if not sentiment_files:
        print("No sentiment analysis files found.")
        return
    
    # Get the most recent file
    latest_file = sorted(sentiment_files)[-1]
    sentiment_file = os.path.join(data_dir, latest_file)
    
    # Load sentiment data
    sentiment_data = pd.read_csv(sentiment_file)
    
    # Create output directory for visualizations
    viz_dir = os.path.join('data', 'visualizations')
    os.makedirs(viz_dir, exist_ok=True)
    
    # Plot overall sentiment by ticker
    output_file = os.path.join(viz_dir, 'sentiment_by_ticker.png')
    plot_sentiment_by_ticker(sentiment_data, output_file)
    
    # Plot sentiment vs price for each ticker
    unique_tickers = sentiment_data['ticker'].unique()
    for ticker in unique_tickers:
        output_file = os.path.join(viz_dir, f'{ticker}_sentiment_vs_price.png')
        plot_sentiment_vs_price(ticker, sentiment_data, output_file=output_file)

if __name__ == "__main__":
    main()