import pandas as pd
import os
import openai
from openai import OpenAI
import time
import json

class SentimentAnalyzer:
    def __init__(self, api_key=None, model="gpt-3.5-turbo"):
        """Initialize the sentiment analyzer with OpenAI API"""
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.model = model
        
        # System prompt optimized for financial sentiment analysis
        self.system_prompt = """You are a financial sentiment analysis expert. 
        Analyze the sentiment of financial news headlines and return your analysis in JSON format.
        
        Consider financial context like:
        - Earnings reports, revenue growth/decline
        - Market volatility, stock price movements  
        - Regulatory changes, company announcements
        - Economic indicators and market trends
        
        Return ONLY a JSON object with these exact keys:
        {
            "sentiment": "positive|negative|neutral",
            "confidence": 0.95,
            "sentiment_score": 0.7
        }
        
        Where:
        - sentiment: positive, negative, or neutral
        - confidence: 0.0 to 1.0 (how confident you are)
        - sentiment_score: -1.0 to 1.0 (negative to positive, 0 is neutral)"""
    
    def analyze_text(self, text):
        """Analyze sentiment of a single text using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Analyze this financial news headline: '{text}'"}
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=100    # Small response expected
            )
            
            # Parse the JSON response
            result_text = response.choices[0].message.content.strip()
            try:
                result = json.loads(result_text)
                return {
                    'text': text,
                    'sentiment': result.get('sentiment', 'neutral'),
                    'confidence': float(result.get('confidence', 0.5)),
                    'sentiment_score': float(result.get('sentiment_score', 0.0))
                }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                print(f"JSON parsing failed for: {result_text}")
                return self._fallback_analysis(text, result_text)
                
        except Exception as e:
            print(f"Error analyzing text '{text[:50]}...': {e}")
            return {
                'text': text,
                'sentiment': 'neutral',
                'confidence': 0.0,
                'sentiment_score': 0.0
            }
    
    def _fallback_analysis(self, text, response_text):
        """Simple fallback analysis if JSON parsing fails"""
        response_lower = response_text.lower()
        if 'positive' in response_lower:
            sentiment = 'positive'
            score = 0.5
        elif 'negative' in response_lower:
            sentiment = 'negative'
            score = -0.5
        else:
            sentiment = 'neutral'
            score = 0.0
            
        return {
            'text': text,
            'sentiment': sentiment,
            'confidence': 0.5,
            'sentiment_score': score
        }
    
    def analyze_dataframe(self, df, text_column, batch_size=5):
        """Analyze sentiment for all texts in a dataframe column with rate limiting"""
        results = []
        texts = df[text_column].fillna('').tolist()
        
        print(f"Analyzing {len(texts)} texts using OpenAI API...")
        
        for i, text in enumerate(texts):
            if i > 0 and i % batch_size == 0:
                print(f"Processed {i}/{len(texts)} texts...")
                time.sleep(1)  # Rate limiting - adjust as needed
            
            if text and text.strip():
                result = self.analyze_text(text)
                results.append(result)
            else:
                results.append({
                    'text': '',
                    'sentiment': 'neutral',
                    'confidence': 0.0,
                    'sentiment_score': 0.0
                })
        
        # Create DataFrame with results
        sentiment_df = pd.DataFrame(results)
        
        # Join with original dataframe
        result_df = pd.concat([df.reset_index(drop=True), sentiment_df.reset_index(drop=True)], axis=1)
        
        # Remove duplicate text column if exists
        if 'text' in result_df.columns and text_column in result_df.columns and text_column != 'text':
            result_df = result_df.drop(columns=['text'])
        
        return result_df


class LightweightSentimentAnalyzer:
    """Alternative using simple rule-based approach for ultra-fast analysis"""
    
    def __init__(self):
        # Financial-specific positive and negative words
        self.positive_words = {
            'growth', 'profit', 'gain', 'rise', 'surge', 'boost', 'strong', 'beat',
            'exceed', 'outperform', 'bullish', 'upgrade', 'success', 'expansion',
            'revenue', 'earnings', 'dividend', 'acquisition', 'merger', 'deal'
        }
        
        self.negative_words = {
            'loss', 'decline', 'drop', 'fall', 'crash', 'plunge', 'weak', 'miss',
            'underperform', 'bearish', 'downgrade', 'failure', 'bankruptcy',
            'debt', 'lawsuit', 'investigation', 'scandal', 'layoffs', 'cuts'
        }
    
    def analyze_text(self, text):
        """Simple rule-based sentiment analysis"""
        text_lower = text.lower()
        words = set(text_lower.split())
        
        positive_count = len(words.intersection(self.positive_words))
        negative_count = len(words.intersection(self.negative_words))
        
        if positive_count > negative_count:
            sentiment = 'positive'
            score = min(0.8, positive_count * 0.2)
        elif negative_count > positive_count:
            sentiment = 'negative'
            score = max(-0.8, -negative_count * 0.2)
        else:
            sentiment = 'neutral'
            score = 0.0
        
        confidence = min(0.9, abs(positive_count - negative_count) * 0.3)
        
        return {
            'text': text,
            'sentiment': sentiment,
            'confidence': confidence,
            'sentiment_score': score
        }
    
    def analyze_dataframe(self, df, text_column):
        """Fast rule-based analysis for entire dataframe"""
        results = []
        
        for text in df[text_column].fillna(''):
            if text and text.strip():
                result = self.analyze_text(text)
                results.append(result)
            else:
                results.append({
                    'text': '',
                    'sentiment': 'neutral',
                    'confidence': 0.0,
                    'sentiment_score': 0.0
                })
        
        sentiment_df = pd.DataFrame(results)
        result_df = pd.concat([df.reset_index(drop=True), sentiment_df.reset_index(drop=True)], axis=1)
        
        if 'text' in result_df.columns and text_column in result_df.columns and text_column != 'text':
            result_df = result_df.drop(columns=['text'])
        
        return result_df


def process_news_data(news_file, output_file=None, use_openai=True, api_key=None):
    """Process news data with sentiment analysis"""
    if not os.path.exists(news_file):
        print(f"File not found: {news_file}")
        return None, None
    
    # Load news data
    df = pd.read_csv(news_file)
    print(f"Loaded {len(df)} news articles")
    
    # Choose analyzer
    if use_openai and (api_key or os.getenv('OPENAI_API_KEY')):
        print("Using OpenAI API for sentiment analysis...")
        analyzer = SentimentAnalyzer(api_key=api_key)
    else:
        print("Using lightweight rule-based sentiment analysis...")
        analyzer = LightweightSentimentAnalyzer()
    
    # Analyze sentiment
    result_df = analyzer.analyze_dataframe(df, 'title')
    
    # Calculate average sentiment by ticker
    ticker_sentiment = result_df.groupby('ticker').agg({
        'sentiment_score': 'mean',
        'title': 'count'
    }).rename(columns={'title': 'article_count'})
    
    print("\nAverage Sentiment by Ticker:")
    print(ticker_sentiment)
    
    # Save results
    if output_file:
        result_df.to_csv(output_file, index=False)
        print(f"Saved sentiment analysis to {output_file}")
    
    return result_df, ticker_sentiment


if __name__ == "__main__":
    # Find the most recent news file
    data_dir = 'data'
    if not os.path.exists(data_dir):
        print(f"Data directory '{data_dir}' not found.")
        exit(1)
    
    news_files = [f for f in os.listdir(data_dir) 
                  if f.startswith('financial_news_') and f.endswith('.csv')]
    
    if not news_files:
        print("No news data files found. Run data collection first.")
        exit(1)
    
    # Get the most recent file
    latest_file = sorted(news_files)[-1] 
    news_file = os.path.join(data_dir, latest_file)
    output_file = os.path.join(data_dir, latest_file.replace('.csv', '_sentiment.csv'))
    
    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Warning: OPENAI_API_KEY not found in environment variables.")
        print("Set it with: export OPENAI_API_KEY='your-api-key-here'")
        print("Falling back to rule-based analysis...")
    
    # Process news data
    process_news_data(news_file, output_file, use_openai=bool(api_key))