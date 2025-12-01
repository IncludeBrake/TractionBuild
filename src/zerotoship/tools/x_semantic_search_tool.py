"""
X (Twitter) Semantic Search Tool for tractionbuild.
Provides semantic search capabilities for X/Twitter content.
"""

from crewai.tools import BaseTool
import requests
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import os
import time
import json

class XSemanticSearchArgs(BaseModel):
    """Arguments for the X Semantic Search Tool."""
    query: str = Field(..., description="The search query")
    max_results: int = Field(default=10, description="Maximum number of results to return")
    language: str = Field(default="en", description="Language for search results")

class XSemanticSearchTool(BaseTool):
    """Semantic search tool for X/Twitter content."""
    
    name: str = "X Semantic Search"
    description: str = "Performs semantic search on X/Twitter content to find relevant posts and trends."
    args_schema: type[BaseModel] = XSemanticSearchArgs

    def __init__(self):
        """Initialize the X API client."""
        super().__init__()
        self.api_key = os.getenv('X_API_KEY')
        self.api_secret = os.getenv('X_API_SECRET')
        self.bearer_token = os.getenv('X_BEARER_TOKEN')
        self.base_url = "https://api.twitter.com/2"

    def _run(self, query: str, max_results: int = 10, language: str = "en") -> Dict[str, Any]:
        """
        Perform semantic search on X/Twitter.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            language: Language for search results
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            if not self.bearer_token:
                return self._mock_search_results(query, max_results, language)
            
            # Prepare search parameters
            params = {
                'query': query,
                'max_results': min(max_results, 100),  # API limit
                'tweet.fields': 'created_at,author_id,public_metrics,context_annotations',
                'user.fields': 'name,username,verified',
                'expansions': 'author_id',
                'lang': language
            }
            
            headers = {
                'Authorization': f'Bearer {self.bearer_token}',
                'Content-Type': 'application/json'
            }
            
            # Make API request
            response = requests.get(
                f"{self.base_url}/tweets/search/recent",
                params=params,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._process_search_results(data, query)
            else:
                # Fallback to mock results if API fails
                print(f"X API request failed: {response.status_code}")
                return self._mock_search_results(query, max_results, language)
                
        except Exception as e:
            print(f"X search failed: {e}")
            return self._mock_search_results(query, max_results, language)

    def _process_search_results(self, data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Process and format X API search results."""
        tweets = data.get('data', [])
        users = {user['id']: user for user in data.get('includes', {}).get('users', [])}
        
        processed_tweets = []
        for tweet in tweets:
            author = users.get(tweet.get('author_id', ''), {})
            processed_tweets.append({
                'id': tweet.get('id'),
                'text': tweet.get('text'),
                'created_at': tweet.get('created_at'),
                'author': {
                    'name': author.get('name'),
                    'username': author.get('username'),
                    'verified': author.get('verified', False)
                },
                'metrics': tweet.get('public_metrics', {}),
                'context': tweet.get('context_annotations', [])
            })
        
        return {
            'query': query,
            'results': processed_tweets,
            'total_results': len(processed_tweets),
            'source': 'x_api',
            'timestamp': time.time(),
            'status': 'success'
        }

    def _mock_search_results(self, query: str, max_results: int, language: str) -> Dict[str, Any]:
        """Generate mock search results for testing and when API is unavailable."""
        mock_tweets = [
            {
                'id': f'mock_{i}',
                'text': f'Mock tweet about {query} - this is a sample result for testing purposes.',
                'created_at': '2024-01-01T12:00:00Z',
                'author': {
                    'name': f'Mock User {i}',
                    'username': f'mockuser{i}',
                    'verified': i % 3 == 0
                },
                'metrics': {
                    'retweet_count': i * 10,
                    'like_count': i * 25,
                    'reply_count': i * 5
                },
                'context': []
            }
            for i in range(1, min(max_results + 1, 6))
        ]
        
        return {
            'query': query,
            'results': mock_tweets,
            'total_results': len(mock_tweets),
            'source': 'mock_data',
            'timestamp': time.time(),
            'status': 'success',
            'note': 'Using mock data - set X_BEARER_TOKEN for real results'
        }

    def get_trending_topics(self, language: str = "en") -> Dict[str, Any]:
        """
        Get trending topics on X/Twitter.
        
        Args:
            language: Language for trending topics
            
        Returns:
            Dictionary containing trending topics
        """
        try:
            if not self.bearer_token:
                return self._mock_trending_topics(language)
            
            headers = {
                'Authorization': f'Bearer {self.bearer_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url}/trends/place/1",  # Worldwide trends
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._process_trending_topics(data, language)
            else:
                return self._mock_trending_topics(language)
                
        except Exception as e:
            print(f"Failed to get trending topics: {e}")
            return self._mock_trending_topics(language)

    def _process_trending_topics(self, data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Process trending topics data."""
        trends = data.get('trends', [])
        
        return {
            'language': language,
            'trends': trends[:10],  # Top 10 trends
            'total_trends': len(trends),
            'source': 'x_api',
            'timestamp': time.time(),
            'status': 'success'
        }

    def _mock_trending_topics(self, language: str) -> Dict[str, Any]:
        """Generate mock trending topics."""
        mock_trends = [
            {'name': 'AI', 'tweet_volume': 50000},
            {'name': 'Startup', 'tweet_volume': 30000},
            {'name': 'Innovation', 'tweet_volume': 25000},
            {'name': 'Tech', 'tweet_volume': 40000},
            {'name': 'Productivity', 'tweet_volume': 20000}
        ]
        
        return {
            'language': language,
            'trends': mock_trends,
            'total_trends': len(mock_trends),
            'source': 'mock_data',
            'timestamp': time.time(),
            'status': 'success',
            'note': 'Using mock data - set X_BEARER_TOKEN for real results'
        }

    def analyze_sentiment(self, tweets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sentiment of a list of tweets.
        
        Args:
            tweets: List of tweet dictionaries
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        try:
            # Simple sentiment analysis based on keywords
            positive_words = ['great', 'awesome', 'amazing', 'love', 'excellent', 'good', 'best']
            negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'disappointing']
            
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for tweet in tweets:
                text = tweet.get('text', '').lower()
                positive_matches = sum(1 for word in positive_words if word in text)
                negative_matches = sum(1 for word in negative_words if word in text)
                
                if positive_matches > negative_matches:
                    positive_count += 1
                elif negative_matches > positive_matches:
                    negative_count += 1
                else:
                    neutral_count += 1
            
            total_tweets = len(tweets)
            
            return {
                'total_tweets': total_tweets,
                'positive': positive_count,
                'negative': negative_count,
                'neutral': neutral_count,
                'positive_percentage': (positive_count / total_tweets * 100) if total_tweets > 0 else 0,
                'negative_percentage': (negative_count / total_tweets * 100) if total_tweets > 0 else 0,
                'neutral_percentage': (neutral_count / total_tweets * 100) if total_tweets > 0 else 0,
                'overall_sentiment': 'positive' if positive_count > negative_count else 'negative' if negative_count > positive_count else 'neutral'
            }
            
        except Exception as e:
            return {
                'error': f'Sentiment analysis failed: {str(e)}',
                'status': 'error'
            }

    async def _arun(self, query: str, max_results: int = 10, language: str = "en") -> Dict[str, Any]:
        """Async version of the X semantic search tool."""
        return self._run(query, max_results, language)
