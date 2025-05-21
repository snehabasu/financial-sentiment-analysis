# Financial Sentiment Analysis

A Python project for analyzing sentiment from financial news and correlating it with stock price movements.

## Features

- Collects financial news from Yahoo Finance
- Fetches stock price data using yfinance
- Analyzes sentiment using FinBERT (a financial domain-specific BERT model)
- Visualizes sentiment vs. stock price
- Interactive dashboard with Streamlit

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/financial-sentiment-analysis.git
cd financial-sentiment-analysis

2. python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. pip install -r requirements.txt

Usage
Data Collection and Analysis
Run the main script to collect and analyze financial news:
python src/main.py