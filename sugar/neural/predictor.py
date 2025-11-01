
#!/usr/bin/env python
"""
Commodity Sentiment and Confidence Predictor using Qwen/Qwen3-32B-LoRa model.
Analyzes news text and returns sentiment classification and confidence scores.
"""

import os
import json
import argparse
from typing import Dict, List, Optional, Tuple, Any
from openai import OpenAI
from datetime import datetime
try:
    from clickhouse_driver import Client
    from sugar.backend.config import CLICKHOUSE_NATIVE_CONFIG
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    CLICKHOUSE_AVAILABLE = False


class CommoditySentimentPredictor:
    """
    A predictor class for analyzing commodity news sentiment and confidence
    using the Qwen/Qwen3-32B-LoRa:my-custom-model-commodity-pedw model.
    """
    
    def __init__(self, api_key: Optional[str] = None, save_prompts: bool = False):
        """
        Initialize the predictor with API credentials.
        
        Args:
            api_key: Nebius API key. If None, will try to get from environment.
            save_prompts: Whether to save prompts to ClickHouse news.prompts table.
        """
        # First try to use the provided api_key, then fall back to environment variable
        self.api_key = api_key
        
        # If no api_key provided, try to get from environment
        if self.api_key is None:
            self.api_key = os.environ.get("NEBIUS_API_KEY")
        
        self.model = "Qwen/Qwen3-32B-LoRa:my-custom-model-commodity-pedw"
        self._client = None
        self._clickhouse_client = None
        self.save_prompts = save_prompts
        
        # Validate that we have a non-empty API key
        if self.api_key is None:
            raise ValueError(
                "NEBIUS_API_KEY environment variable not set and no api_key provided. "
                "Please set the NEBIUS_API_KEY environment variable or provide an api_key parameter."
            )
        
        # Check if the API key is empty or just whitespace
        if not self.api_key.strip():
            raise ValueError(
                "NEBIUS_API_KEY is empty or contains only whitespace. "
                "Please provide a valid API key."
            )
        
        # Trim whitespace from the API key
        self.api_key = self.api_key.strip()
        
        if self.save_prompts and not CLICKHOUSE_AVAILABLE:
            raise ImportError("ClickHouse dependencies not available. Install clickhouse-driver and ensure config is accessible.")
    
    @property
    def client(self):
        """Lazy initialization of the OpenAI client."""
        if self._client is None:
            self._client = OpenAI(
                base_url="https://api.studio.nebius.com/v1/",
                api_key=self.api_key
            )
        return self._client
    
    @property
    def clickhouse_client(self):
        """Lazy initialization of the ClickHouse client."""
        if self._clickhouse_client is None and self.save_prompts:
            self._clickhouse_client = Client(**CLICKHOUSE_NATIVE_CONFIG)
        return self._clickhouse_client
    
    def _create_system_prompt(self) -> str:
        """
        Create the system prompt for sentiment analysis.
        
        Returns:
            System prompt string
        """
        return """You are a specialized commodity market sentiment analysis expert. Your task is to analyze news articles and provide:

1. **Sentiment Classification**: Classify the sentiment as one of:
   - "positive" - indicates bullish/optimistic outlook for commodity prices
   - "negative" - indicates bearish/pessimistic outlook for commodity prices
   - "neutral" - indicates balanced/no clear directional bias

2. **Confidence Score**: A numerical score between 0.0 and 1.0 indicating your confidence in the sentiment classification, where:
   - 1.0 = extremely high confidence
   - 0.8-0.9 = high confidence
   - 0.6-0.7 = moderate confidence
   - 0.4-0.5 = low confidence
   - <0.4 = very low confidence

3. **Reasoning**: A brief explanation of your analysis, highlighting key factors that influenced your decision.

Focus on factors such as:
- Supply and demand dynamics
- Weather and crop conditions (for agricultural commodities)
- Geopolitical events
- Economic indicators
- Market sentiment and trader positioning
- Production and consumption data
- Inventory levels
- Price trends and technical factors

Respond in JSON format with the following structure:
{
  "sentiment": "positive|negative|neutral",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of the analysis"
}"""

    def _create_user_prompt(self, text: str, title: Optional[str] = None, commodity: Optional[str] = None, topics: Optional[List[str]] = None, datetime: Optional[datetime] = None) -> str:
        """
        Create the user prompt with the text to analyze.
        
        Args:
            text: The main text content to analyze
            title: Optional title/headline of the article
            commodity: Optional commodity type for context
            topics: Optional list of topics for context
            datetime: Optional datetime when the article was created
            
        Returns:
            User prompt string
        """
        prompt_parts = []
        
        if commodity:
            prompt_parts.append(f"Commodity: {commodity}")
        
        if title:
            prompt_parts.append(f"Title: {title}")
        
        if datetime:
            prompt_parts.append(f"Date: {datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if topics:
            prompt_parts.append(f"Topics: {', '.join(topics)}")
        
        prompt_parts.append(f"Text to analyze:\n{text}")
        
        return "\n\n".join(prompt_parts)
    
    def analyze_sentiment(self, text: str, title: Optional[str] = None, commodity: Optional[str] = None, topics: Optional[List[str]] = None, article_id: Optional[str] = None, datetime: Optional[datetime] = None) -> Dict:
        """
        Analyze sentiment and confidence for the given text.
        
        Args:
            text: The text content to analyze
            title: Optional title/headline for context
            commodity: Optional commodity type for context
            topics: Optional list of topics for context
            article_id: Optional article ID for saving prompts
            datetime: Optional datetime when the article was created
            
        Returns:
            Dictionary containing sentiment, confidence, and reasoning
        """
        if not text or not text.strip():
            raise ValueError("Text to analyze cannot be empty")
        
        # Create prompts
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt(text, title, commodity, topics, datetime)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=500
            )
            
            # Extract the response content
            response_content = response.choices[0].message.content
            
            print(f"DEBUG: Raw response content: {repr(response_content)}")
            
            # Try to parse as JSON
            try:
                # Find the start of the JSON object
                json_start = response_content.find('{')
                if json_start == -1:
                    raise ValueError("No JSON object found in response")
                
                # Extract the JSON portion
                json_content = response_content[json_start:]
                print(f"DEBUG: Extracted JSON content: {repr(json_content)}")
                
                # Try to parse with standard JSON first
                try:
                    result = json.loads(json_content)
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Standard JSON parsing failed: {e}")
                    
                    # As a fallback, manually extract the values using regex
                    import re
                    
                    # Extract sentiment - handle both single and double quotes
                    sentiment_match = re.search(r'"sentiment"\s*:\s*["\']([^"\']*)["\']', json_content)
                    sentiment = sentiment_match.group(1) if sentiment_match else 'neutral'
                    
                    # Extract confidence
                    confidence_match = re.search(r'"confidence"\s*:\s*([0-9.]+)', json_content)
                    confidence = float(confidence_match.group(1)) if confidence_match else 0.5
                    
                    # Extract reasoning - use a more robust pattern that handles escaped quotes
                    reasoning_match = re.search(r'"reasoning"\s*:\s*"((?:[^"\\]|\\.)*)"', json_content)
                    if reasoning_match:
                        reasoning = reasoning_match.group(1)
                        # Unescape common escape sequences
                        reasoning = reasoning.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
                    else:
                        # Try with single quotes
                        reasoning_match = re.search(r'"reasoning"\s*:\s*' + r"'((?:[^'\\]|\\.)*)'", json_content)
                        if reasoning_match:
                            reasoning = reasoning_match.group(1)
                            # Unescape common escape sequences
                            reasoning = reasoning.replace('\\n', '\n').replace('\\t', '\t').replace("\\'", "'")
                        else:
                            reasoning = 'No reasoning provided'
                    
                    # Create result manually
                    result = {
                        'sentiment': sentiment,
                        'confidence': confidence,
                        'reasoning': reasoning
                    }
                    
                    print(f"DEBUG: Manually extracted result: {result}")
                
                print(f"DEBUG: Successfully parsed JSON: {result}")
                
                # Validate the response structure
                if not all(key in result for key in ['sentiment', 'confidence', 'reasoning']):
                    raise ValueError("Response missing required fields")
                
                # Validate sentiment value
                if result['sentiment'] not in ['positive', 'negative', 'neutral']:
                    raise ValueError(f"Invalid sentiment value: {result['sentiment']}")
                
                # Validate confidence range
                if not (0.0 <= result['confidence'] <= 1.0):
                    raise ValueError(f"Confidence score out of range: {result['confidence']}")
                
                # Save prompts to ClickHouse if enabled
                if self.save_prompts and article_id:
                    self._save_prompts_to_clickhouse(
                        article_id=article_id,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        response=response_content,
                        sentiment=result['sentiment'],
                        confidence=result['confidence'],
                        reasoning=result['reasoning'],
                        title=title,
                        commodity=commodity,
                        topics=topics,
                        datetime=datetime
                    )
                
                return result
                
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON decode error: {e}")
                
                # If response is not valid JSON, check if it contains JSON within the text
                # Sometimes the model returns JSON with extra text before or after
                if '{' in response_content and '}' in response_content:
                    try:
                        # Extract JSON part from the response
                        json_start = response_content.find('{')
                        json_end = response_content.rfind('}') + 1
                        json_str = response_content[json_start:json_end]
                        
                        print(f"DEBUG: Extracted JSON string: {repr(json_str)}")
                        
                        result = json.loads(json_str)
                        print(f"DEBUG: Successfully parsed extracted JSON: {result}")
                        
                        # Validate the response structure
                        if not all(key in result for key in ['sentiment', 'confidence', 'reasoning']):
                            raise ValueError("Response missing required fields")
                        
                        # Validate sentiment value
                        if result['sentiment'] not in ['positive', 'negative', 'neutral']:
                            raise ValueError(f"Invalid sentiment value: {result['sentiment']}")
                        
                        # Validate confidence range
                        if not (0.0 <= result['confidence'] <= 1.0):
                            raise ValueError(f"Confidence score out of range: {result['confidence']}")
                        
                        # Save prompts to ClickHouse if enabled
                        if self.save_prompts and article_id:
                            self._save_prompts_to_clickhouse(
                                article_id=article_id,
                                system_prompt=system_prompt,
                                user_prompt=user_prompt,
                                response=response_content,
                                sentiment=result['sentiment'],
                                confidence=result['confidence'],
                                reasoning=result['reasoning'],
                                title=title,
                                commodity=commodity,
                                topics=topics,
                                datetime=datetime
                            )
                        
                        return result
                    except (json.JSONDecodeError, ValueError) as e2:
                        print(f"DEBUG: Error parsing extracted JSON: {e2}")
                        # If JSON extraction fails, fall back to text parsing
                        pass
                
                # If response is not valid JSON and couldn't extract JSON, try to extract information manually
                parsed_result = self._parse_text_response(response_content)
                print(f"DEBUG: Using parsed text response: {parsed_result}")
                
                # Save prompts to ClickHouse if enabled
                if self.save_prompts and article_id:
                    self._save_prompts_to_clickhouse(
                        article_id=article_id,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        response=response_content,
                        sentiment=parsed_result['sentiment'],
                        confidence=parsed_result['confidence'],
                        reasoning=parsed_result['reasoning'],
                        title=title,
                        commodity=commodity,
                        topics=topics,
                        datetime=datetime
                    )
                
                return parsed_result
                
        except Exception as e:
            raise RuntimeError(f"Error during sentiment analysis: {str(e)}")
    
    def _parse_text_response(self, response_text: str) -> Dict:
        """
        Fallback method to parse non-JSON responses.
        
        Args:
            response_text: Raw response text from the model
            
        Returns:
            Dictionary with extracted sentiment, confidence, and reasoning
        """
        # Default values
        result = {
            'sentiment': 'neutral',
            'confidence': 0.5,
            'reasoning': 'Could not parse structured response'
        }
        
        response_lower = response_text.lower()
        
        # Extract sentiment
        if 'positive' in response_lower or 'bullish' in response_lower:
            result['sentiment'] = 'positive'
        elif 'negative' in response_lower or 'bearish' in response_lower:
            result['sentiment'] = 'negative'
        
        # Try to extract confidence (look for numbers between 0 and 1)
        import re
        confidence_matches = re.findall(r'confidence[:\s]*(0?\.\d+|1\.0)', response_lower)
        if confidence_matches:
            try:
                result['confidence'] = float(confidence_matches[0])
            except ValueError:
                pass
        
        # Use the response as reasoning
        result['reasoning'] = response_text[:500]  # Limit length
        
        return result
    
    def batch_analyze(self, texts: List[str], titles: Optional[List[str]] = None,
                     commodities: Optional[List[str]] = None, topics_list: Optional[List[List[str]]] = None,
                     article_ids: Optional[List[str]] = None, datetimes: Optional[List[datetime]] = None) -> List[Dict]:
        """
        Analyze sentiment for multiple texts in batch.
        
        Args:
            texts: List of text contents to analyze
            titles: Optional list of titles (must match texts length)
            commodities: Optional list of commodities (must match texts length)
            topics_list: Optional list of topics lists (must match texts length)
            article_ids: Optional list of article IDs (must match texts length)
            datetimes: Optional list of datetimes (must match texts length)
            
        Returns:
            List of analysis results
        """
        if not texts:
            return []
        
        results = []
        
        for i, text in enumerate(texts):
            title = titles[i] if titles and i < len(titles) else None
            commodity = commodities[i] if commodities and i < len(commodities) else None
            topics = topics_list[i] if topics_list and i < len(topics_list) else None
            article_id = article_ids[i] if article_ids and i < len(article_ids) else None
            datetime_obj = datetimes[i] if datetimes and i < len(datetimes) else None
            
            try:
                result = self.analyze_sentiment(text, title, commodity, topics, article_id, datetime_obj)
                results.append(result)
            except Exception as e:
                # Add error result but continue processing
                results.append({
                    'sentiment': 'neutral',
                    'confidence': 0.0,
                    'reasoning': f'Error processing text: {str(e)}',
                    'error': str(e)
                })
        
        return results
    
    def _save_prompts_to_clickhouse(self, article_id: str, system_prompt: str, user_prompt: str,
                                   response: str, sentiment: str, confidence: float, reasoning: str,
                                   title: Optional[str] = None, commodity: Optional[str] = None,
                                   topics: Optional[List[str]] = None, datetime: Optional[datetime] = None) -> bool:
        """
        Save prompts and analysis results to ClickHouse news.prompts table.
        
        Args:
            article_id: ID of the article
            system_prompt: System prompt sent to the model
            user_prompt: User prompt sent to the model
            response: Response from the model
            sentiment: Sentiment classification
            confidence: Confidence score
            reasoning: Reasoning for the sentiment
            title: Optional article title
            commodity: Optional commodity type
            topics: Optional list of topics
            datetime: Optional datetime when the article was created
            
        Returns:
            True if successful, False otherwise
        """
        if not self.save_prompts:
            return False
        
        try:
            # Check if prompts table exists, create if not
            self._ensure_prompts_table_exists()
            
            # Prepare data for insertion
            created_at = datetime.now()
            topics_json = json.dumps(topics) if topics else None
            
            # Insert data
            self.clickhouse_client.execute(
                'INSERT INTO news.prompts (article_id, system_prompt, user_prompt, response, '
                'sentiment, confidence, reasoning, title, commodity, topics, created_at) VALUES',
                [(article_id, system_prompt, user_prompt, response, sentiment, confidence,
                  reasoning, title, commodity, topics_json, created_at)]
            )
            
            return True
            
        except Exception as e:
            print(f"Error saving prompts to ClickHouse: {str(e)}")
            return False
    
    def _ensure_prompts_table_exists(self) -> None:
        """
        Ensure that the news.prompts table exists in ClickHouse.
        Create it if it doesn't exist.
        """
        try:
            # Check if table exists
            tables = self.clickhouse_client.execute("SHOW TABLES FROM news")
            table_names = [table[0] for table in tables]
            
            if 'prompts' not in table_names:
                # Create the prompts table
                create_table_query = """
                CREATE TABLE news.prompts (
                    article_id String,
                    system_prompt String,
                    user_prompt String,
                    response String,
                    sentiment String,
                    confidence Float32,
                    reasoning String,
                    title Nullable(String),
                    commodity Nullable(String),
                    topics Nullable(String),
                    created_at DateTime
                ) ENGINE = MergeTree()
                ORDER BY (article_id, created_at)
                """
                
                self.clickhouse_client.execute(create_table_query)
                print("Created news.prompts table in ClickHouse")
            
        except Exception as e:
            print(f"Error ensuring prompts table exists: {str(e)}")
            raise


def main():
    """
    Main function for command-line usage.
    """
    parser = argparse.ArgumentParser(description="Analyze commodity news sentiment using Qwen model")
    parser.add_argument('--text', type=str, help='Text to analyze')
    parser.add_argument('--title', type=str, help='Optional title/headline')
    parser.add_argument('--commodity', type=str, default='Sugar', help='Commodity type (default: Sugar)')
    parser.add_argument('--topics', type=str, help='Comma-separated list of topics')
    parser.add_argument('--datetime', type=str, help='Article datetime in ISO format (YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--file', type=str, help='Input file containing text to analyze')
    parser.add_argument('--output', type=str, help='Output file for results (JSON format)')
    parser.add_argument('--save-prompts', action='store_true', help='Save prompts to ClickHouse news.prompts table')
    parser.add_argument('--article-id', type=str, help='Article ID for saving prompts')
    
    args = parser.parse_args()
    
    # Parse topics if provided
    topics = None
    if args.topics:
        topics = [topic.strip() for topic in args.topics.split(',')]
    
    # Parse datetime if provided
    datetime_obj = None
    if args.datetime:
        try:
            datetime_obj = datetime.strptime(args.datetime, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                # Try alternative format
                datetime_obj = datetime.strptime(args.datetime, '%Y-%m-%d')
            except ValueError:
                print(f"Warning: Invalid datetime format '{args.datetime}'. Expected format: YYYY-MM-DD HH:MM:SS or YYYY-MM-DD")
    
    # Initialize predictor
    try:
        predictor = CommoditySentimentPredictor(save_prompts=args.save_prompts)
    except ValueError as e:
        print(f"Error initializing predictor: {e}")
        return 1
    
    # Get text to analyze
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f"Error reading input file: {e}")
            return 1
    elif args.text:
        text = args.text
    else:
        # Interactive mode
        print("Enter text to analyze (Ctrl+D to finish):")
        try:
            text = ''.join(line for line in sys.stdin)
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return 0
    
    if not text.strip():
        print("Error: No text provided for analysis")
        return 1
    
    # Perform analysis
    try:
        result = predictor.analyze_sentiment(text, args.title, args.commodity, topics, args.article_id, datetime_obj)
        
        # Format output
        output = {
            'analysis': result,
            'metadata': {
                'model': predictor.model,
                'commodity': args.commodity,
                'title': args.title,
                'topics': topics,
                'datetime': datetime_obj.isoformat() if datetime_obj else None,
                'text_length': len(text)
            }
        }
        
        # Output results
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=2, ensure_ascii=False)
                print(f"Results saved to: {args.output}")
            except Exception as e:
                print(f"Error saving output file: {e}")
                return 1
        else:
            print("\n=== Sentiment Analysis Results ===")
            print(f"Sentiment: {result['sentiment'].upper()}")
            print(f"Confidence: {result['confidence']:.2f}")
            print(f"Reasoning: {result['reasoning']}")
            print(f"\nModel: {predictor.model}")
            print(f"Commodity: {args.commodity}")
        
        return 0
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1


if __name__ == "__main__":
    import sys
    exit(main())

