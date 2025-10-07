import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
from textblob import TextBlob
import logging

class AdvancedSentimentAnalyzer:
    def __init__(self):
        # Financial keywords with weights
        self.positive_keywords = {
            'profit': 3, 'growth': 2, 'revenue': 2, 'expansion': 2, 'acquisition': 2,
            'bullish': 3, 'surge': 3, 'rally': 3, 'breakthrough': 3, 'milestone': 2,
            'outperform': 3, 'beat': 2, 'exceed': 2, 'strong': 2, 'robust': 2,
            'upgrade': 3, 'buy': 3, 'investment': 1, 'dividend': 2, 'bonus': 2,
            'launch': 1, 'innovative': 2, 'success': 2, 'positive': 1, 'gain': 2
        }
        
        self.negative_keywords = {
            'loss': -3, 'decline': -2, 'fall': -2, 'drop': -2, 'crash': -3,
            'bearish': -3, 'plunge': -3, 'collapse': -3, 'bankruptcy': -4, 'debt': -2,
            'underperform': -3, 'miss': -2, 'weak': -2, 'poor': -2, 'concern': -1,
            'downgrade': -3, 'sell': -3, 'risk': -1, 'challenge': -1, 'trouble': -2,
            'fraud': -4, 'scandal': -4, 'investigation': -2, 'penalty': -2, 'fine': -2
        }
        
        self.impact_multipliers = {
            'quarterly': 1.5, 'annual': 1.3, 'results': 1.4, 'earnings': 1.4,
            'guidance': 1.3, 'forecast': 1.2, 'outlook': 1.2, 'target': 1.1
        }
    
    def analyze_advanced_sentiment(self, text):
        """Perform advanced sentiment analysis with financial context"""
        text_lower = text.lower()
        
        # Calculate keyword-based sentiment
        keyword_score = self._calculate_keyword_sentiment(text_lower)
        
        # TextBlob sentiment as baseline
        blob = TextBlob(text)
        textblob_score = blob.sentiment.polarity
        
        # Combine scores (70% keyword, 30% TextBlob)
        combined_score = (keyword_score * 0.7) + (textblob_score * 0.3)
        
        # Apply impact multipliers
        multiplier = self._get_impact_multiplier(text_lower)
        final_score = combined_score * multiplier
        
        # Convert to categorical sentiment
        if final_score > 0.1:
            sentiment = "Positive"
        elif final_score < -0.1:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"
        
        return {
            'sentiment': sentiment,
            'confidence': abs(final_score),
            'raw_score': final_score,
            'keyword_contribution': keyword_score,
            'textblob_contribution': textblob_score,
            'impact_multiplier': multiplier
        }
    
    def _calculate_keyword_sentiment(self, text):
        """Calculate sentiment based on financial keywords"""
        score = 0
        word_count = len(text.split())
        
        # Positive keywords
        for keyword, weight in self.positive_keywords.items():
            count = len(re.findall(r'\b' + keyword + r'\b', text))
            score += count * weight
        
        # Negative keywords
        for keyword, weight in self.negative_keywords.items():
            count = len(re.findall(r'\b' + keyword + r'\b', text))
            score += count * weight
        
        # Normalize by text length
        # FIX 1: Reduced multiplier from 100 to 10. The original value caused the score
        # to saturate at -1 or 1 too quickly, losing nuance. This provides a more granular score.
        normalized_score = score / max(word_count, 1) * 10
        return np.tanh(normalized_score)  # Bounded between -1 and 1
    
    def _get_impact_multiplier(self, text):
        """Get impact multiplier based on context"""
        multiplier = 1.0
        
        for keyword, mult in self.impact_multipliers.items():
            if keyword in text:
                multiplier = max(multiplier, mult)
        
        return multiplier

class TradingSignalGenerator:
    def __init__(self):
        self.signal_weights = {
            'sentiment': 0.4,
            'price_momentum': 0.3,
            'volume': 0.2,
            'technical': 0.1
        }
    
    def generate_trading_signal(self, sentiment_data, stock_data, technical_data=None):
        """Generate comprehensive trading signal"""
        signals = {}
        
        # Sentiment signal
        sentiment_signal = self._sentiment_to_signal(sentiment_data)
        signals['sentiment'] = sentiment_signal
        
        # Price momentum signal
        if stock_data:
            momentum_signal = self._price_momentum_signal(stock_data)
            # FIX 2: Changed key from 'momentum' to 'price_momentum' to match the
            # self.signal_weights dictionary. This ensures the correct weight (0.3) is applied.
            signals['price_momentum'] = momentum_signal
            
            # Volume signal
            volume_signal = self._volume_signal(stock_data)
            
            # FIX 3: Made volume directional. Raw volume is just magnitude, but for a trading
            # signal, it should be negative on down days and positive on up days.
            if momentum_signal != 0:
                volume_signal *= np.sign(momentum_signal)

            signals['volume'] = volume_signal
        
        # Technical signal (if available)
        if technical_data is not None:
            tech_signal = self._technical_signal(technical_data)
            signals['technical'] = tech_signal
        
        # Calculate overall signal
        overall_signal = self._calculate_overall_signal(signals)
        
        return {
            'overall_signal': overall_signal,
            'signal_strength': abs(overall_signal),
            'individual_signals': signals,
            'recommendation': self._signal_to_recommendation(overall_signal),
            'confidence_level': self._calculate_confidence(signals)
        }
    
    def _sentiment_to_signal(self, sentiment_data):
        """Convert sentiment to trading signal"""
        sentiment = sentiment_data['sentiment']
        confidence = sentiment_data['confidence']
        
        if sentiment == 'Positive':
            return confidence
        elif sentiment == 'Negative':
            return -confidence
        else:
            return 0
    
    def _price_momentum_signal(self, stock_data):
        """Generate signal based on price momentum"""
        change_pct = stock_data.get('change_percent', 0)
        
        # Normalize percentage change to signal (-1 to 1)
        signal = np.tanh(change_pct / 5)  # 5% change = ~0.76 signal
        return signal
    
    def _volume_signal(self, stock_data):
        """Generate signal based on volume (simplified)"""
        # This is a simplified version - in reality, you'd compare with historical volume
        volume = stock_data.get('volume', 0)
        
        # Assume higher volume is more significant
        if volume > 1000000:  # High volume
            return 0.5
        elif volume > 100000:  # Medium volume
            return 0.2
        else:  # Low volume
            return 0
    
    def _technical_signal(self, technical_data):
        """Generate signal from technical indicators"""
        if technical_data is None or technical_data.empty:
            return 0
        
        latest = technical_data.iloc[-1]
        signals = []
        
        # RSI signal
        rsi = latest.get('RSI')
        if pd.notna(rsi):
            if rsi > 70:
                signals.append(-0.5)  # Overbought
            elif rsi < 30:
                signals.append(0.5)   # Oversold
            else:
                signals.append(0)
        
        # Moving average signal
        close = latest.get('Close')
        ma_20 = latest.get('MA_20')
        ma_50 = latest.get('MA_50')
        
        if pd.notna(close) and pd.notna(ma_20) and pd.notna(ma_50):
            if close > ma_20 > ma_50:
                signals.append(0.3)   # Bullish
            elif close < ma_20 < ma_50:
                signals.append(-0.3)  # Bearish
            else:
                signals.append(0)
        
        return np.mean(signals) if signals else 0
    
    def _calculate_overall_signal(self, signals):
        """Calculate weighted overall signal"""
        weighted_sum = 0
        total_weight = 0
        
        for signal_type, value in signals.items():
            weight = self.signal_weights.get(signal_type, 0.1)
            weighted_sum += value * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0
    
    def _signal_to_recommendation(self, signal):
        """Convert numerical signal to recommendation"""
        if signal > 0.3:
            return "Strong Buy"
        elif signal > 0.1:
            return "Buy"
        elif signal > -0.1:
            return "Hold"
        elif signal > -0.3:
            return "Sell"
        else:
            return "Strong Sell"
    
    def _calculate_confidence(self, signals):
        """Calculate confidence in the signal"""
        # Higher confidence when signals agree
        signal_values = list(signals.values())
        if not signal_values:
            return 0
        
        # Standard deviation - lower is better (signals agree)
        std_dev = np.std(signal_values)
        mean_abs = np.mean([abs(x) for x in signal_values])
        
        # Confidence is higher when signals are strong and agree
        confidence = mean_abs * (1 - min(std_dev, 1))
        return min(confidence, 1.0)

class NewsImpactCalculator:
    def __init__(self):
        self.impact_categories = {
            'earnings': {'keywords': ['earnings', 'results', 'quarterly', 'annual'], 'multiplier': 1.5},
            'acquisition': {'keywords': ['acquisition', 'merger', 'takeover', 'buyout'], 'multiplier': 2.0},
            'regulatory': {'keywords': ['regulatory', 'approval', 'license', 'compliance'], 'multiplier': 1.3},
            'product': {'keywords': ['launch', 'product', 'service', 'innovation'], 'multiplier': 1.2},
            'financial': {'keywords': ['debt', 'loan', 'funding', 'investment', 'ipo'], 'multiplier': 1.4},
            'management': {'keywords': ['ceo', 'cfo', 'director', 'appointment', 'resignation'], 'multiplier': 1.1}
        }
    
    def calculate_impact_score(self, title, content, sentiment_data):
        """Calculate the potential market impact of news"""
        text = (title + " " + content).lower()
        
        # Base impact from sentiment
        base_impact = sentiment_data['confidence']
        
        # Category multiplier
        category_multiplier = 1.0
        detected_categories = []
        
        # This 'for' loop contains the line that was previously incomplete and causing the error
        for category, info in self.impact_categories.items():
            if any(keyword in text for keyword in info['keywords']):
                category_multiplier = max(category_multiplier, info['multiplier'])
                detected_categories.append(category)
        
        # Final impact score
        impact_score = base_impact * category_multiplier

        return {
            'impact_score': impact_score,
            'base_sentiment_confidence': base_impact,
            'category_multiplier': category_multiplier,
            'detected_categories': detected_categories if detected_categories else ['general']
        }

if __name__ == "__main__":
    # --- 1. Instantiate Analyzers ---
    sentiment_analyzer = AdvancedSentimentAnalyzer()
    signal_generator = TradingSignalGenerator()
    impact_calculator = NewsImpactCalculator()

    # --- 2. Sample Data ---
    # Sample News Article
    news_title = "TechCorp Inc. Announces Record Quarterly Earnings, Exceeding Forecasts"
    news_content = """
    TechCorp Inc. today reported a massive profit for the fourth quarter, with revenue growth surging by 25%.
    This success is attributed to the recent launch of their innovative product line and a major acquisition.
    The company's outlook for the next annual period is extremely positive. However, some analysts express concern over rising debt levels.
    """

    # Sample Stock Data for the Day
    stock_data = {'change_percent': 3.5, 'volume': 1_200_000}

    # Sample Technical Data (e.g., from a library like TA-Lib)
    technical_data = pd.DataFrame({
        'Date': [datetime.now() - timedelta(days=1)],
        'Close': [155.0],
        'RSI': [65.0],  # Neither overbought nor oversold
        'MA_20': [152.0],
        'MA_50': [148.0]
    })

    # --- 3. Run Analysis ---
    print("📰 ANALYZING NEWS ARTICLE...")
    # Analyze sentiment of the news
    sentiment_result = sentiment_analyzer.analyze_advanced_sentiment(news_title + " " + news_content)
    
    # Calculate the news impact
    impact_result = impact_calculator.calculate_impact_score(news_title, news_content, sentiment_result)
    
    # Generate a trading signal based on all available data
    trading_signal = signal_generator.generate_trading_signal(sentiment_result, stock_data, technical_data)
    
    # --- 4. Display Results ---
    print("\n" + "="*50)
    print("📊 SENTIMENT ANALYSIS RESULTS")
    print("-"*50)
    print(f"  Sentiment: {sentiment_result['sentiment']}")
    print(f"  Confidence Score: {sentiment_result['confidence']:.4f}")
    print(f"  Raw Score: {sentiment_result['raw_score']:.4f}")
    print(f"  Keyword Contribution: {sentiment_result['keyword_contribution']:.4f}")
    print(f"  TextBlob Contribution: {sentiment_result['textblob_contribution']:.4f}")
    print(f"  Impact Multiplier: {sentiment_result['impact_multiplier']:.2f}")

    print("\n" + "="*50)
    print("💥 NEWS IMPACT ASSESSMENT")
    print("-"*50)
    print(f"  Detected Categories: {', '.join(impact_result['detected_categories'])}")
    print(f"  Category Multiplier: {impact_result['category_multiplier']:.2f}")
    print(f"  Final Impact Score: {impact_result['impact_score']:.4f} (out of a max determined by the multiplier)")

    print("\n" + "="*50)
    print("📈 TRADING SIGNAL & RECOMMENDATION")
    print("-"*50)
    print(f"  Overall Signal: {trading_signal['overall_signal']:.4f} (from -1 to 1)")
    print(f"  Signal Strength: {trading_signal['signal_strength']:.4f}")
    print(f"  System Confidence: {trading_signal['confidence_level']:.4f}")
    print(f"  RECOMMENDATION: ** {trading_signal['recommendation']} **")
    print("\n  --- Signal Breakdown ---")
    for source, value in trading_signal['individual_signals'].items():
        print(f"    - {source.replace('_', ' ').capitalize()} Signal: {value:.4f}")
    print("="*50)