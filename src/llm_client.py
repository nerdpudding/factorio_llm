"""
Ollama LLM Client.

Wrapper for Ollama's /api/chat endpoint with tool calling support.
"""

import requests
from typing import Any

from .config import Config


class OllamaClient:
    """Client for Ollama API (local or cloud)."""

    def __init__(self, config: Config):
        """
        Initialize with config.

        Args:
            config: Config object with ollama_url, model, etc.
        """
        self.config = config
        self.base_url = config.ollama_url.rstrip("/")

    def _get_headers(self) -> dict[str, str]:
        """Get request headers, including auth if API key is set."""
        headers = {"Content-Type": "application/json"}
        if self.config.ollama_api_key:
            headers["Authorization"] = f"Bearer {self.config.ollama_api_key}"
        return headers

    def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
        debug: bool = False,
    ) -> dict[str, Any]:
        """
        Send chat request to Ollama.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                      Roles: 'system', 'user', 'assistant', 'tool'
            tools: Optional list of tool definitions for function calling.

        Returns:
            Response dict with:
                - message: The assistant's response message
                - tool_calls: List of tool calls (if any)

        Raises:
            ConnectionError: If Ollama is not reachable.
            RuntimeError: If API returns an error.
        """
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "num_ctx": self.config.num_ctx,
                "num_predict": self.config.num_predict,
            },
        }

        # Add tools if provided
        if tools:
            payload["tools"] = tools

        # Add think parameter at top level (for thinking models like Qwen3, DeepSeek)
        # Only send if explicitly configured (None = let Ollama decide)
        if self.config.think is not None:
            payload["think"] = self.config.think

        try:
            response = requests.post(
                url, json=payload, headers=self._get_headers(), timeout=120
            )
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Is Ollama running?"
            ) from e
        except requests.exceptions.Timeout as e:
            raise RuntimeError("Ollama request timed out after 120s") from e

        if response.status_code != 200:
            raise RuntimeError(
                f"Ollama API error {response.status_code}: {response.text}"
            )

        data = response.json()

        if debug:
            msg = data.get("message", {})
            print(f"  [OLLAMA] content: {msg.get('content', '')[:100]}")
            print(f"  [OLLAMA] tool_calls: {msg.get('tool_calls')}")
            # Show thinking if present (for thinking models)
            if msg.get("thinking"):
                print(f"  [OLLAMA] thinking: {msg.get('thinking', '')[:100]}...")
            # Show actual token counts from Ollama
            prompt_tokens = data.get("prompt_eval_count", 0)
            output_tokens = data.get("eval_count", 0)
            print(f"  [OLLAMA] tokens: {prompt_tokens} prompt + {output_tokens} output = {prompt_tokens + output_tokens} total")

        # Extract the response
        result = {
            "message": data.get("message", {}),
            "tool_calls": None,
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "output_tokens": data.get("eval_count", 0),
        }

        # Check for tool calls in the response
        if "message" in data and "tool_calls" in data["message"]:
            result["tool_calls"] = data["message"]["tool_calls"]

        return result

    def is_available(self) -> bool:
        """
        Check if Ollama is reachable.

        Returns:
            True if Ollama responds, False otherwise.
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                headers=self._get_headers(),
                timeout=5,
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def list_models(self) -> list[str]:
        """
        List available models.

        Returns:
            List of model names.
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                headers=self._get_headers(),
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except requests.exceptions.RequestException:
            pass
        return []

    def unload_model(self) -> bool:
        """
        Unload the current model from GPU memory.

        Sends a request with keep_alive=0 to free VRAM.

        Returns:
            True if successful, False otherwise.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.config.model,
            "prompt": "",
            "keep_alive": 0,
        }
        try:
            response = requests.post(
                url, json=payload, headers=self._get_headers(), timeout=30
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
