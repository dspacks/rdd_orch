import time
import random
import logging
import os
from typing import List, Optional

try:
    from google import genai
except ImportError:
    genai = None

from ..config import APIConfig, API_CONFIG
from ..models import Snippet

logger = logging.getLogger('ADE.BaseAgent')

class BaseAgent:
    """
    Enhanced base agent using the google-genai SDK (v1.0+) with:
    - Smart retry logic with exponential backoff and jitter
    - Rate limit header parsing
    - Better error handling
    """

    def __init__(self, name: str, system_prompt: str, config: APIConfig = None):
        self.name = name
        self.system_prompt = system_prompt
        self.config = config or API_CONFIG
        
        self.client = None
        try:
            if genai:
                # API Key is automatically picked up from GOOGLE_API_KEY environment variable
                self.client = genai.Client()
            else:
                logger.warning("google-genai SDK not found. LLM functionality will be disabled.")
        except Exception as e:
            logger.warning(f"Failed to initialize GenAI Client: {e}")
            
        self.active_snippets: List[Snippet] = []
        self.last_request_time = 0
        self.request_count = 0
        self.logger = logger

    def _wait_for_rate_limit(self):
        """Implement rate limiting by waiting if necessary."""
        if self.last_request_time > 0:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.config.min_delay:
                wait_time = self.config.min_delay - elapsed
                time.sleep(wait_time)

    def _get_retry_delay_with_jitter(self, attempt: int, base_delay: float = None) -> float:
        """Calculate exponential backoff delay with jitter."""
        if base_delay is None:
            base_delay = self.config.base_retry_delay

        # Exponential backoff: base_delay * (2 ^ attempt)
        delay = base_delay * (2 ** attempt)

        # Add jitter: randomize between 50% and 100% of the calculated delay
        jitter = delay * (0.5 + random.random() * 0.5)

        # Cap maximum delay at 60 seconds
        return min(jitter, 60.0)

    def _parse_rate_limit_headers(self, error) -> Optional[float]:
        """Try to extract retry-after time from error response."""
        # Note: google-genai errors might differ structure from old SDK. 
        # We'll use a generic approach for now until error shapes are confirmed.
        return None

    def generate(self, prompt: str) -> str:
        """Generate content with smart retry logic."""
        return self.generate_with_smart_retry(prompt)

    def generate_with_smart_retry(self, prompt: str) -> str:
        """
        Generate content using google-genai SDK.
        """
        if not self.client:
             # Fallback/mock for environments without API key or during migration test
            if os.environ.get("MOCK_LLM", "false").lower() == "true":
                return f"[MOCK OUTPUT] Processed: {prompt[:50]}..."
            raise RuntimeError("GenAI Client not initialized. Check imports and API Key.")

        last_error = None
        full_prompt = f"{self.system_prompt}\n\n{prompt}"

        for attempt in range(self.config.max_retries):
            try:
                self._wait_for_rate_limit()
                
                # Execute generation using the new Client pattern
                # models.generate_content(model=..., contents=...)
                response = self.client.models.generate_content(
                    model=self.config.model_name,
                    contents=full_prompt
                )
                
                self.last_request_time = time.time()
                self.request_count += 1
                
                if not response.text:
                    raise ValueError("Empty response from model")
                    
                return response.text

            except Exception as e:
                last_error = e
                # Error handling logic remains similar but might need adapting to new exceptions
                # For now simple exponential backoff
                delay = self._get_retry_delay_with_jitter(attempt)
                self.logger.warning(f"Generation error (attempt {attempt+1}): {e}. Retrying in {delay:.1f}s")
                time.sleep(delay)

        raise last_error or Exception(f"Max retries ({self.config.max_retries}) exceeded")
