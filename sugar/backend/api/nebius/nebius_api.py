import os
import time
import random
import httpx
from openai import OpenAI
from typing import Optional

class NebiusAPI:
    """
    Nebius API client for generating text using Qwen models.
    Enhanced with better error handling and connection management.
    """
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 60):
        """
        Initialize the NebiusAPI client.
        
        Args:
            api_key: Optional API key. If not provided, uses NEBIUS_API_KEY from environment.
            timeout: Request timeout in seconds (default: 60)
        """
        self.api_key = api_key or os.getenv('NEBIUS_API_KEY')
        if not self.api_key:
            raise ValueError("No API key provided and NEBIUS_API_KEY not found in environment variables.")
        
        self.timeout = timeout
        
        # Create httpx client with retry logic
        self.http_client = httpx.Client(
            timeout=timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
        self.client = OpenAI(
            base_url="https://api.studio.nebius.ai/v1/",
            api_key=self.api_key,
            http_client=self.http_client
        )
    
    def generate_text(self, prompt: str, model_name: str = "Qwen/Qwen2.5-72B-Instruct", 
                     max_tokens: int = 1000, temperature: float = 0.3, 
                     max_retries: int = 3) -> Optional[str]:
        """
        Generate text using the specified model with retry logic.
        
        Args:
            prompt: The input prompt
            model_name: Name of the model to use
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation (0.0 to 1.0)
            max_retries: Maximum number of retry attempts
            
        Returns:
            Generated text or None if failed
        """
        for attempt in range(max_retries):
            try:
                # Add small delay between retries
                if attempt > 0:
                    delay = 2 ** attempt + random.uniform(0, 1)
                    time.sleep(delay)
                
                messages = [{"role": "user", "content": prompt}]
                
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                if response.choices and response.choices[0].message:
                    return response.choices[0].message.content
                else:
                    print(f"Attempt {attempt + 1}: Empty response from API")
                    if attempt == max_retries - 1:
                        return None
                    continue
                
            except httpx.ConnectError as e:
                print(f"Attempt {attempt + 1}: Connection error: {e}")
                if attempt == max_retries - 1:
                    print(f"Connection failed after {max_retries} attempts")
                    return None
                continue
                
            except httpx.TimeoutException as e:
                print(f"Attempt {attempt + 1}: Timeout error: {e}")
                if attempt == max_retries - 1:
                    print(f"Request timed out after {max_retries} attempts")
                    return None
                continue
                
            except httpx.HTTPError as e:
                print(f"Attempt {attempt + 1}: HTTP error: {e}")
                if attempt == max_retries - 1:
                    print(f"HTTP request failed after {max_retries} attempts")
                    return None
                continue
                
            except Exception as e:
                error_msg = str(e)
                if "rate limit" in error_msg.lower() or "429" in error_msg:
                    print(f"Attempt {attempt + 1}: Rate limit hit, waiting...")
                    time.sleep(5 + random.uniform(0, 5))  # Wait 5-10 seconds
                    continue
                elif "timeout" in error_msg.lower():
                    print(f"Attempt {attempt + 1}: Timeout: {e}")
                    if attempt == max_retries - 1:
                        return None
                    continue
                else:
                    print(f"Attempt {attempt + 1}: Unexpected error: {e}")
                    if attempt == max_retries - 1:
                        return None
                    continue
        
        return None
    
    def test_connection(self) -> bool:
        """
        Test the connection to the Nebius API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            test_prompt = "Hello, this is a connection test. Please respond with 'OK'."
            response = self.generate_text(
                prompt=test_prompt,
                model_name="Qwen/Qwen2.5-72B-Instruct",
                max_tokens=10,
                temperature=0.1,
                max_retries=1
            )
            return response is not None
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def __del__(self):
        """Clean up the HTTP client"""
        if hasattr(self, 'http_client'):
            self.http_client.close() 