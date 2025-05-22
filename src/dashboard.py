import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import yfinance as yf
import sys

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import project modules
import sentiment
import data_collection

# Set page config
st.set_page_config(
    page_title="Financial Sentiment Dashboard",
    page_icon="📈",
    layout="wide"
)

def load_latest_data():
    """Load the most recent sentiment and stock data"""
    data_dir = 'data'
    
    # Find sentiment files
    sentiment_files = [f for f in os.listdir(data_dir) 
                      if f.endswith('_sentiment.csv')]
    
    if not sentiment_files:
        return None, []
    
    # Get the most recent file
    latest_file = sorted(sentiment_files)[-1]
    sentiment_file = os.path.join(data_dir, latest_file)
    
    # Load sentiment data
    sentiment_data = pd.read_csv(sentiment_file)
    
    # Get unique tickers
    tickers = sentiment_data['ticker'].unique().tolist()
    
    return sentiment_data, tickers

def analyze_new_ticker(ticker):
    """Collect and analyze data for a new ticker"""
    # Get stock data
    stock_data = data_collection.get_stock_data(ticker)
    data_collection.save_stock_data(ticker, stock_data)
    
    # Get news
    news = data_collection.get_financial_news(ticker, max_articles=10)
    
    if not news:
        st.error(f"No news found for {ticker}")
        return None
    
    # Save news data
    news_df = pd.DataFrame(news)
    
    # Analyze sentiment
    analyzer = sentiment.SentimentAnalyzer()
    result_df = analyzer.analyze_dataframe(news_df, 'title')
    
    return result_df

def main():
    st.title("Financial Sentiment Analysis Dashboard")
    
    # Load existing data
    sentiment_data, available_tickers = load_latest_data()
    
    # Sidebar
    st.sidebar.header("Controls")
    
    # Add new ticker
    new_ticker = st.sidebar.text_input("Analyze new ticker", "").upper()
    if st.sidebar.button("Add Ticker"):
        if new_ticker and len(new_ticker) <= 5:
            with st.spinner(f"Analyzing {new_ticker}..."):
                new_data = analyze_new_ticker(new_ticker)
                if new_data is not None:
                    if sentiment_data is not None:
                        sentiment_data = pd.concat([sentiment_data, new_data])
                    else:
                        sentiment_data = new_data
                    if new_ticker not in available_tickers:
                        available_tickers.append(new_ticker)
        else:
            st.sidebar.error("Please enter a valid ticker symbol")
    
    # If no data is available
    if sentiment_data is None or sentiment_data.empty:
        st.info("No sentiment data available. Please add a ticker to analyze.")
        return
    
    # Select ticker to display
    selected_ticker = st.sidebar.selectbox(
        "Select Ticker",
        available_tickers
    )
    
    # Filter data for selected ticker
    ticker_data = sentiment_data[sentiment_data['ticker'] == selected_ticker]
    
    # Calculate average sentiment
    avg_sentiment = ticker_data['sentiment_score'].mean()
    sentiment_color = "green" if avg_sentiment > 0 else "red"
    
    # Main dashboard area
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Sentiment Overview")
        st.metric(
            label=f"{selected_ticker} Sentiment Score", 
            value=f"{avg_sentiment:.2f}",
            delta=f"{avg_sentiment:.2f}"
        )
        
        # Distribution of sentiments
        sentiment_counts = ticker_data['sentiment'].value_counts()
        
        # Prepare data for pie chart
        labels = sentiment_counts.index
        sizes = sentiment_counts.values
        colors = ['red', 'gray', 'green']
        
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)
    
    with col2:
        st.subheader("Stock Price vs. Sentiment")
        
        # Get stock data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        stock_data = yf.download(selected_ticker, start=start_date, end=end_date)
        
        # Create figure with two y-axes
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # Plot stock price
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Stock Price ($)', color='tab:blue')
        ax1.plot(stock_data.index, stock_data['Close'], color='tab:blue', label='Stock Price')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        
        # Create second y-axis
        ax2 = ax1.twinx()
        ax2.set_ylabel('Sentiment Score', color='tab:red')
        
        # Convert published date to datetime if needed
        if 'published_date' not in ticker_data.columns:
            try:
                ticker_data['published_date'] = pd.to_datetime(ticker_data['published'])
            except:
                # If we can't parse the dates, just use retrieved_date
                ticker_data['published_date'] = pd.to_datetime(ticker_data['retrieved_date'])
        
        # Plot sentiment as scatter points
        ax2.scatter(ticker_data['published_date'], ticker_data['sentiment_score'], 
                    color='tab:red', alpha=0.7, label='News Sentiment')
        ax2.tick_params(axis='y', labelcolor='tab:red')
        
        # Add title
        plt.title(f'{selected_ticker}: Stock Price vs. News Sentiment')
        
        # Create combined legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Format x-axis date labels
        fig.autofmt_xdate()
        
        st.pyplot(fig)
    
    # Recent news
    st.subheader("Recent News")
    
    # Sort by date if available
    if 'published_date' in ticker_data.columns:
        ticker_data = ticker_data.sort_values('published_date', ascending=False)
    
    for _, row in ticker_data.head(5).iterrows():
        sentiment_icon = "🟢" if row['sentiment'] == 'positive' else "🔴" if row['sentiment'] == 'negative' else "⚪"
        st.write(f"{sentiment_icon} **{row['title']}** ({row['sentiment']}, {row['confidence']:.2f})")
        st.write(f"Source: {row['source']} | [Read More]({row['url']})")
        st.write("---")

if __name__ == "__main__":
    main()