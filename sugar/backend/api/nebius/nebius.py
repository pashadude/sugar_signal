from openai import OpenAI
import re
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple, Dict, Any
import itertools

class NebiusBatchAPI:
    """
    Generic Nebius batch API caller for LLM prompts.
    Accepts a list of prompts, a model name, and a list of API keys.
    Returns a list of raw outputs (one per prompt).
    """
    def __init__(self, api_keys: List[str], model: str = "Qwen/Qwen3-235B-A22B", temperature: float = 0.0, top_p: float = 0.95):
        if not api_keys:
            raise ValueError("At least one API key must be provided.")
        self.api_keys = api_keys
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        # Prepare a round-robin iterator for API keys
        self.api_key_cycle = itertools.cycle(api_keys)

    def call_single_prompt(self, prompt: str) -> Dict[str, Any]:
        api_key = next(self.api_key_cycle)
        client = OpenAI(
            base_url="https://api.studio.nebius.ai/v1/",
            api_key=api_key
        )
        messages = [
            {"role": "user", "content": prompt}
        ]
        try:
            response = client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                top_p=self.top_p,
                messages=messages
            )
            content = response.choices[0].message.content
            return {"output": content, "success": True}
        except Exception as e:
            return {"output": str(e), "success": False}

    def batch_call(self, prompts: List[str], max_workers: int = 10) -> List[Dict[str, Any]]:
        """
        Call Nebius LLM API for a batch of prompts.
        Returns a list of dicts with 'output' and 'success' fields.
        """
        with ThreadPoolExecutor(max_workers=min(max_workers, len(prompts))) as executor:
            futures = [
                executor.submit(self.call_single_prompt, prompt)
                for prompt in prompts
            ]
            results = [future.result() for future in futures]
        return results
