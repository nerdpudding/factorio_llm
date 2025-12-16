"""
Central configuration for Factorio LLM.

Loads settings from config.yaml and provides a Config dataclass.
Supports both old format (direct model settings) and new format (model profiles).
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# Cloud API URL for Mode C (Fully Cloud)
# Note: Don't include /api suffix - the client adds /api/... paths
OLLAMA_CLOUD_API_URL = "https://ollama.com"


@dataclass
class Config:
    """Central configuration loaded from YAML."""

    # Ollama
    ollama_url: str
    model: str
    temperature: float
    top_p: float
    num_ctx: int
    num_predict: int
    think: bool | None  # None = don't send parameter (let Ollama decide)

    # Agent
    max_tool_iterations: int
    max_history_messages: int
    max_prompt_history: int  # Limit for .factorio_chat_history file (0 = unlimited)

    # RCON
    rcon_host: str
    rcon_port: int
    rcon_password: str

    # Optional fields (must come after required fields in dataclass)
    ollama_api_key: str | None = None  # For Mode C (Fully Cloud)
    available_models: dict[str, dict[str, Any]] = field(default_factory=dict)
    active_model_key: str = ""

    @classmethod
    def from_yaml(cls, path: str | Path = None) -> "Config":
        """
        Load config from YAML file.

        Supports two formats:
        1. New format (model profiles):
           models:
             ministral:
               name: ministral-3:14b-instruct-2512-q8_0
               temperature: 0.15
               ...
           active_model: ministral

        2. Old format (backwards compatible):
           model: ministral-3:14b-instruct-2512-q8_0
           temperature: 0.15
           ...

        Args:
            path: Path to config file. Defaults to config.yaml in project root.

        Returns:
            Config instance with loaded values.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            KeyError: If required config key is missing.
            ValueError: If active_model references unknown profile.
        """
        if path is None:
            # Default to config.yaml in project root
            path = Path(__file__).parent.parent / "config.yaml"
        else:
            path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Detect format: new (models dict) vs old (direct model)
        if "models" in data and "active_model" in data:
            # New format with model profiles
            return cls._from_new_format(data)
        else:
            # Old format (backwards compatible)
            return cls._from_old_format(data)

    @classmethod
    def _from_new_format(cls, data: dict) -> "Config":
        """Load from new format with model profiles."""
        active_key = data["active_model"]
        models = data["models"]

        if active_key not in models:
            available = ", ".join(models.keys())
            raise ValueError(
                f"Unknown model profile '{active_key}'. "
                f"Available: {available}"
            )

        profile = models[active_key]

        # API key: config file takes precedence, then env var
        api_key = data.get("ollama_api_key") or os.environ.get("OLLAMA_API_KEY")

        return cls(
            # Ollama (from active profile)
            ollama_url=data["ollama_url"],
            model=profile["name"],
            temperature=profile["temperature"],
            top_p=profile.get("top_p", 1.0),
            num_ctx=profile["num_ctx"],
            num_predict=profile["num_predict"],
            think=profile.get("think"),  # None if not specified
            ollama_api_key=api_key,
            # Agent
            max_tool_iterations=data["max_tool_iterations"],
            max_history_messages=data.get("max_history_messages", 20),
            max_prompt_history=data.get("max_prompt_history", 500),
            # RCON
            rcon_host=data["rcon_host"],
            rcon_port=data["rcon_port"],
            rcon_password=data["rcon_password"],
            # Model profiles for runtime switching
            available_models=models,
            active_model_key=active_key,
        )

    @classmethod
    def _from_old_format(cls, data: dict) -> "Config":
        """Load from old format (backwards compatible)."""
        # API key: config file takes precedence, then env var
        api_key = data.get("ollama_api_key") or os.environ.get("OLLAMA_API_KEY")

        return cls(
            # Ollama
            ollama_url=data["ollama_url"],
            model=data["model"],
            temperature=data["temperature"],
            top_p=data.get("top_p", 1.0),  # Default if not specified
            num_ctx=data["num_ctx"],
            num_predict=data["num_predict"],
            think=data.get("think"),  # None if not specified
            ollama_api_key=api_key,
            # Agent
            max_tool_iterations=data["max_tool_iterations"],
            max_history_messages=data.get("max_history_messages", 20),
            max_prompt_history=data.get("max_prompt_history", 500),
            # RCON
            rcon_host=data["rcon_host"],
            rcon_port=data["rcon_port"],
            rcon_password=data["rcon_password"],
            # No profiles in old format
            available_models={},
            active_model_key="",
        )

    def switch_model(self, profile_key: str) -> None:
        """
        Switch to a different model profile.

        Args:
            profile_key: Key from available_models dict.

        Raises:
            ValueError: If profile_key is unknown or no profiles available.
        """
        if not self.available_models:
            raise ValueError("No model profiles available (using old config format)")

        if profile_key not in self.available_models:
            available = ", ".join(self.available_models.keys())
            raise ValueError(
                f"Unknown model profile '{profile_key}'. "
                f"Available: {available}"
            )

        profile = self.available_models[profile_key]
        self.model = profile["name"]
        self.temperature = profile["temperature"]
        self.top_p = profile.get("top_p", 1.0)
        self.num_ctx = profile["num_ctx"]
        self.num_predict = profile["num_predict"]
        self.think = profile.get("think")
        self.active_model_key = profile_key

    def __repr__(self) -> str:
        """String representation (hides password)."""
        return (
            f"Config(model={self.model!r}, "
            f"ollama_url={self.ollama_url!r}, "
            f"rcon_host={self.rcon_host!r}, "
            f"rcon_port={self.rcon_port})"
        )
