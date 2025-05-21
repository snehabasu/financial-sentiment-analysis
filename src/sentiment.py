import pandas as pd
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np

class SentimentAnalyzer:
    def __init__(self, model_name="ProsusAI/finbert"):
        """Initialize the sentiment analyzer with a pre-trained model"""
        print(f"Loading model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        # FinBERT labels: negative (0), neutral (1), positive (2)
        self.labels = ["negative", "neutral", "positive"]
    
    def analyze_text(self, text):
        """Analyze sentiment of a single text"""
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
        sentiment_idx = torch.argmax(probabilities, dim=1).item()
        
        return {
            'text': text,
            'sentiment': self.labels[sentiment_idx],
            'confidence': probabilities[0][sentiment_idx].item(),
            'sentiment_score': self._calculate_sentiment_score(probabilities[0].tolist())
        }
    
    def _calculate_sentiment_score(self, probabilities):
        """Convert probabilities to a single score between -1 and 1"""
        # Negative: -1, Neutral: 0, Positive: 1
        # Weight by probabilities
        return probabilities[2] - probabilities[0]
    
    def analyze_dataframe(self, df, text_column):
        """Analyze sentiment for all texts in a dataframe column"""
        results = []
        
        for text in df[text_column]:
            if pd.notna(text) and text.strip():  # Check if text is not empty
                result = self.analyze_text(text)
                results.append(result)
            else:
                results.append({
                    'text': '',
                    'sentiment': 'neutral',
                    'confidence': 0.0,
                    'sentiment_score': 0.0
                })
        
        # Create a DataFrame with results
        sentiment_df = pd.DataFrame(results)
        
        # Join with the original dataframe
        result_df = pd.concat([df.reset_index(drop=True), sentiment_df.reset_index(drop=True)], axis=1)
        
        # Remove duplicate text column
        if 'text' in result_df and text_column in result_df and text_column != 'text':
            result_df = result_df.drop(columns=['text'])
            
        return result_df

def process_news_data(news_file, output_file=None):
    """Process news data with sentiment analysis"""
    if not os.path.exists(news_file):
        print(f"File not found: {news_file}")
        return None
    
    # Load news data
    df = pd.read_csv(news_file)
    
    # Initialize sentiment analyzer
    analyzer = SentimentAnalyzer()
    
    # Analyze sentiment for news titles
    result_df = analyzer.analyze_dataframe(df, 'title')
    
    # Calculate average sentiment by ticker
    ticker_sentiment = result_df.groupby('ticker').agg({
        'sentiment_score': 'mean',
        'title': 'count'
    }).rename(columns={'title': 'article_count'})
    
    print("\nAverage Sentiment by Ticker:")
    print(ticker_sentiment)
    
    # Save results if output file is provided
    if output_file:
        result_df.to_csv(output_file, index=False)
        print(f"Saved sentiment analysis to {output_file}")
    
    return result_df, ticker_sentiment

def main():
    # Find the most recent news file
    data_dir = 'data'
    news_files = [f for f in os.listdir(data_dir) if f.startswith('financial_news_') and f.endswith('.csv')]
    
    if not news_files:
        print("No news data files found.")
        return
    
    # Get the most recent file
    latest_file = sorted(news_files)[-1]
    news_file = os.path.join(data_dir, latest_file)
    
    # Output file
    output_file = os.path.join(data_dir, latest_file.replace('.csv', '_sentiment.csv'))
    
    # Process news data
    process_news_data(news_file, output_file)

if __name__ == "__main__":
    main()