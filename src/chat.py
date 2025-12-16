"""
Interactive Factorio chat.

Usage:
    conda activate factorio
    cd D:\factorio_llm
    python src/chat.py
"""

import sys
import textwrap
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import colorama for colored output
try:
    from colorama import init, Fore, Style
    init()  # Initialize colorama for Windows
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False

# Try to import prompt_toolkit for enhanced input
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.styles import Style as PTStyle
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False


# Color helper functions (fallback to no color if colorama not available)
def cyan(text: str) -> str:
    return f"{Fore.CYAN}{text}{Style.RESET_ALL}" if COLORS_AVAILABLE else text


def green(text: str) -> str:
    return f"{Fore.GREEN}{text}{Style.RESET_ALL}" if COLORS_AVAILABLE else text


def red(text: str) -> str:
    return f"{Fore.RED}{text}{Style.RESET_ALL}" if COLORS_AVAILABLE else text


def yellow(text: str) -> str:
    return f"{Fore.YELLOW}{text}{Style.RESET_ALL}" if COLORS_AVAILABLE else text


def dim(text: str) -> str:
    return f"{Style.DIM}{text}{Style.RESET_ALL}" if COLORS_AVAILABLE else text


from src.config import Config, OLLAMA_CLOUD_API_URL
from src.llm_client import OllamaClient
import os
from src.factorio_tools import FactorioTools
from src.factorio_agent import FactorioAgent
from src.tool_definitions import FACTORIO_TOOLS


# Commands for tab completion
CHAT_COMMANDS = [
    '/help', '/tools', '/status', '/model', '/models',
    '/switch', '/clear', '/debug', '/quit', '/exit'
]


# Custom completer (only defined if prompt_toolkit is available)
if PROMPT_TOOLKIT_AVAILABLE:
    class CommandCompleter(Completer):
        """Custom completer that only suggests commands when input starts with /."""

        def get_completions(self, document, complete_event):
            text = document.text_before_cursor.lstrip()

            # Only complete if text starts with /
            if not text.startswith('/'):
                return

            # Find matching commands
            for cmd in CHAT_COMMANDS:
                if cmd.startswith(text.lower()):
                    yield Completion(
                        cmd,
                        start_position=-len(text),
                        display_meta='command'
                    )


def trim_history_file(history_file: Path, max_entries: int) -> None:
    """
    Trim history file to keep only the last max_entries lines.

    Args:
        history_file: Path to the history file.
        max_entries: Maximum number of entries to keep. 0 = unlimited.
    """
    if max_entries <= 0 or not history_file.exists():
        return

    try:
        with open(history_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if len(lines) > max_entries:
            # Keep only the last max_entries lines
            lines = lines[-max_entries:]
            with open(history_file, "w", encoding="utf-8") as f:
                f.writelines(lines)
    except Exception:
        pass  # Silently ignore errors (history is not critical)


def create_prompt_session(max_history: int = 500):
    """
    Create a prompt_toolkit session with history, auto-suggest, and completion.

    Args:
        max_history: Maximum history entries to keep (0 = unlimited).

    Returns None if prompt_toolkit is not available (falls back to input()).
    """
    if not PROMPT_TOOLKIT_AVAILABLE:
        return None

    # History file in project directory
    history_file = Path(__file__).parent.parent / '.factorio_chat_history'

    # Trim history file if it exceeds max_history
    trim_history_file(history_file, max_history)

    # Style for the prompt and auto-suggest
    style = PTStyle.from_dict({
        'prompt': 'cyan',
        'auto-suggest': 'fg:ansigray italic',  # Gray italic for suggestions
    })

    return PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
        completer=CommandCompleter(),
        style=style,
    )


HELP_TEXT = """
Available commands:
  /help           - Show this help message
  /tools          - List available Factorio tools
  /status         - Show connection status and player position
  /model          - Show current model info
  /models         - List available model profiles
  /switch <name>  - Switch to a different model profile
  /clear          - Clear conversation history
  /debug          - Toggle debug mode (show tool calls)
  /quit           - Exit the chat
  /exit           - Exit the chat
"""


def format_response(text: str, width: int = 70) -> str:
    """Format a response with proper line wrapping and color."""
    prefix = green("Assistant> ")
    indent = " " * 11  # Length of "Assistant> " without color codes

    # Split into paragraphs
    paragraphs = text.split("\n")
    formatted_lines = []

    for i, para in enumerate(paragraphs):
        if not para.strip():
            formatted_lines.append("")
            continue

        # Wrap the paragraph
        if i == 0:
            # First line gets the colored prefix
            wrapped = textwrap.fill(
                para,
                width=width,
                initial_indent="",
                subsequent_indent=indent,
            )
            formatted_lines.append(prefix + wrapped)
        else:
            # Continuation lines get indentation
            wrapped = textwrap.fill(
                para,
                width=width,
                initial_indent=indent,
                subsequent_indent=indent,
            )
            formatted_lines.append(wrapped)

    return "\n".join(formatted_lines)


def show_tools():
    """Display all available tools with descriptions."""
    print("\nAvailable Factorio tools:")
    print("-" * 50)
    for tool in FACTORIO_TOOLS:
        name = tool["function"]["name"]
        desc = tool["function"]["description"].split(".")[0]  # First sentence only
        print(f"  {name}")
        print(f"    {desc}")
    print()


def select_deployment_mode(config: "Config") -> str:
    """
    Show deployment mode selection menu at startup.

    Returns:
        Deployment mode: 'local', 'local_cloud', or 'fully_cloud'
    """
    print("\nHow do you want to run inference?")
    print("-" * 40)
    print("  1. Local GPU (requires Ollama + GPU with VRAM)")
    print("     " + dim("Your machine runs everything locally"))
    print()
    print("  2. Ollama Cloud (cloud inference)")
    print("     " + dim("No local GPU required"))
    print()

    try:
        choice = input("Enter choice [1-2]: ").strip()
        if choice == "1" or choice == "":
            return "local"
        elif choice == "2":
            # Sub-menu for cloud options
            print()
            print("Cloud setup:")
            print("-" * 40)
            print("  a. Local Ollama + Cloud models")
            print("     " + dim("Requires: ollama signin (one-time)"))
            print()
            print("  b. Fully Cloud (API key required)")
            print("     " + dim("No local Ollama needed"))
            print()

            sub_choice = input("Enter choice [a-b]: ").strip().lower()
            if sub_choice == "a" or sub_choice == "":
                return "local_cloud"
            elif sub_choice == "b":
                return "fully_cloud"
            else:
                print(yellow("Invalid choice, using Local Ollama + Cloud."))
                return "local_cloud"
        else:
            print(yellow("Invalid choice, using Local GPU."))
            return "local"
    except KeyboardInterrupt:
        print("\n")
        raise


def configure_for_fully_cloud(config: "Config") -> bool:
    """
    Configure for Mode C (Fully Cloud) - no local Ollama needed.

    Updates config.ollama_url and validates API key.

    Returns:
        True if configuration succeeded, False if missing API key.
    """
    # Check for API key (config takes precedence over env var)
    api_key = config.ollama_api_key or os.environ.get("OLLAMA_API_KEY")

    if not api_key:
        print()
        print(red("[ERROR] API key required for Fully Cloud mode."))
        print()
        print("Options:")
        print("  1. Set environment variable: OLLAMA_API_KEY=your_key_here")
        print("  2. Add to config.yaml: ollama_api_key: your_key_here")
        print()
        print("Get your API key at: https://ollama.com (account settings)")
        return False

    # Update config to point to cloud API
    config.ollama_url = OLLAMA_CLOUD_API_URL
    config.ollama_api_key = api_key

    print(green("Configured for Fully Cloud mode."))
    print(dim(f"API endpoint: {OLLAMA_CLOUD_API_URL}"))
    return True


def filter_models_by_mode(config: "Config", mode: str) -> None:
    """
    Filter available_models based on deployment mode.

    For local mode: only show non-cloud models.
    For cloud modes: only show cloud models.
    """
    if not config.available_models:
        return

    if mode == "local":
        # Filter out cloud models (names ending in -cloud)
        local_models = {
            k: v for k, v in config.available_models.items()
            if not k.endswith("-cloud")
        }
        if local_models:
            config.available_models = local_models
            # If active model is a cloud model, switch to first local
            if config.active_model_key not in local_models:
                first_key = list(local_models.keys())[0]
                config.switch_model(first_key)
    else:
        # Cloud mode: show only cloud models
        cloud_models = {
            k: v for k, v in config.available_models.items()
            if k.endswith("-cloud")
        }
        if cloud_models:
            config.available_models = cloud_models
            # Switch to first cloud model
            if config.active_model_key not in cloud_models:
                first_key = list(cloud_models.keys())[0]
                config.switch_model(first_key)


def select_model_menu(config: "Config") -> None:
    """Show model selection menu at startup."""
    if not config.available_models:
        return  # No profiles, skip menu

    models = list(config.available_models.keys())
    if len(models) <= 1:
        return  # Only one model, skip menu

    print("\nSelect model:")
    print("-" * 40)
    for i, key in enumerate(models, 1):
        profile = config.available_models[key]
        print(f"  {i}. {key}: {profile['name']}")
        extras = []
        if key == config.active_model_key:
            extras.append("default")
        if profile.get("think"):
            extras.append("thinking")
        if extras:
            print(f"      ({', '.join(extras)})")

    print()
    try:
        choice = input(f"Enter number [1-{len(models)}] or press Enter for default: ").strip()
        if choice == "":
            pass  # Use default, continue to session config
        else:
            num = int(choice)
            if 1 <= num <= len(models):
                selected_key = models[num - 1]
                if selected_key != config.active_model_key:
                    config.switch_model(selected_key)
                    print(green(f"Selected: {config.model}"))
            else:
                print(yellow("Invalid choice, using default."))

        # Session configuration (6.9)
        configure_session_overrides(config)

    except ValueError:
        print(yellow("Invalid input, using default."))
    except KeyboardInterrupt:
        print("\n")
        raise


def configure_session_overrides(config: "Config") -> None:
    """
    Allow user to tweak think/num_ctx for this session without editing config.yaml.

    Shows current settings and offers to customize.
    """
    # Show current settings
    think_status = "on" if config.think else "off"
    print(dim(f"\nCurrent settings: think={think_status}, num_ctx={config.num_ctx}"))

    try:
        customize = input("Customize for this session? [y/N]: ").strip().lower()
        if customize != "y":
            return  # Use defaults

        # Ask about thinking
        if config.think:
            disable_think = input("Disable thinking? (faster) [y/N]: ").strip().lower()
            if disable_think == "y":
                config.think = False
                print(dim("  Thinking disabled for this session"))
        else:
            enable_think = input("Enable thinking? (smarter) [y/N]: ").strip().lower()
            if enable_think == "y":
                config.think = True
                print(dim("  Thinking enabled for this session"))

        # Ask about context size
        print(f"\nContext size options: [1] 4096  [2] 8192  [3] 16384  [4] keep {config.num_ctx}")
        ctx_choice = input("Choose [1-4] or Enter to keep: ").strip()
        ctx_map = {"1": 4096, "2": 8192, "3": 16384}
        if ctx_choice in ctx_map:
            config.num_ctx = ctx_map[ctx_choice]
            print(dim(f"  Context size set to {config.num_ctx}"))

        # Show final settings
        think_status = "on" if config.think else "off"
        print(green(f"\nSession settings: think={think_status}, num_ctx={config.num_ctx}"))

    except KeyboardInterrupt:
        print("\n")
        raise


def main():
    """Main entry point for interactive chat."""
    print("=" * 60)
    print("FACTORIO CHAT")
    print("=" * 60)

    # Load config
    config = Config.from_yaml()

    # Deployment mode selection
    mode = select_deployment_mode(config)

    # Configure for Fully Cloud if selected
    if mode == "fully_cloud":
        if not configure_for_fully_cloud(config):
            return 1  # Missing API key, exit

    # Filter models based on deployment mode
    filter_models_by_mode(config, mode)

    # Model selection menu
    select_model_menu(config)

    # Connect to Ollama
    print(dim("\nConnecting to Ollama..."))
    llm = OllamaClient(config)
    if not llm.is_available():
        print(red("[ERROR] Cannot connect to Ollama. Is it running?"))
        return 1
    print(f"Using model: {config.model}")

    # Connect to Factorio
    print(dim("Connecting to Factorio..."))
    try:
        tools = FactorioTools(
            host=config.rcon_host,
            port=config.rcon_port,
            password=config.rcon_password,
        )
        tools.connect()
        tick = tools.get_tick()
        pos = tools.get_player_position()
        tool_count = len(FACTORIO_TOOLS)
        print(f"Connected to Factorio (tick: {tick}, {tool_count} tools available)")
        print(f"Player position: X={pos.x:.1f}, Y={pos.y:.1f}")
    except Exception as e:
        print(red(f"[ERROR] Cannot connect to Factorio: {e}"))
        print(red("        Make sure Factorio is running in Host Game mode"))
        return 1

    # Create agent
    agent = FactorioAgent(config, llm, tools)

    print("\nType /help for commands, /quit to exit.")
    if PROMPT_TOOLKIT_AVAILABLE:
        print(dim("(↑/↓ for history, Tab for commands)\n"))
    else:
        print()

    # Create prompt session (None if prompt_toolkit not available)
    session = create_prompt_session(max_history=config.max_prompt_history)

    # Main loop
    try:
        while True:
            # Get user input (with prompt_toolkit or fallback to input())
            try:
                if session:
                    # prompt_toolkit: history, autocomplete, suggestions
                    user_input = session.prompt([('class:prompt', 'You> ')]).strip()
                else:
                    # Fallback: basic input
                    user_input = input(cyan("You> ")).strip()
            except EOFError:
                break

            # Skip empty input
            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                cmd = user_input.lower()

                if cmd in ["/quit", "/exit"]:
                    break

                elif cmd == "/help":
                    print(HELP_TEXT)

                elif cmd == "/tools":
                    show_tools()

                elif cmd == "/model":
                    print(f"\nModel: {config.model}")
                    if config.active_model_key:
                        print(f"Profile: {config.active_model_key}")
                    print(f"Temperature: {config.temperature}")
                    print(f"Top-p: {config.top_p}")
                    print(f"Context window: {config.num_ctx}")
                    print()

                elif cmd == "/clear":
                    agent.clear_history()
                    print("Conversation history cleared.\n")

                elif cmd == "/debug":
                    agent.debug = not agent.debug
                    status = "ON" if agent.debug else "OFF"
                    print(f"Debug mode: {status}\n")

                elif cmd == "/status":
                    try:
                        tick = tools.get_tick()
                        pos = tools.get_player_position()
                        tool_count = len(FACTORIO_TOOLS)
                        print(f"\nConnection: OK")
                        print(f"Game tick: {tick}")
                        print(f"Player: X={pos.x:.1f}, Y={pos.y:.1f}")
                        print(f"Model: {config.model}")
                        print(f"Tools: {tool_count} available")
                        print(f"Debug: {'ON' if agent.debug else 'OFF'}")
                        print()
                    except Exception as e:
                        print(red(f"\n[ERROR] Connection issue: {e}\n"))

                elif cmd == "/models":
                    if config.available_models:
                        print("\nAvailable model profiles:")
                        for key, profile in config.available_models.items():
                            marker = "*" if key == config.active_model_key else " "
                            print(f"  {marker} {key}: {profile['name']}")
                        print(f"\nUse /switch <name> to change models.\n")
                    else:
                        print("\nNo model profiles configured (using legacy config format).\n")

                elif cmd.startswith("/switch "):
                    profile_key = user_input[8:].strip()  # Extract profile name
                    if not profile_key:
                        print("Usage: /switch <profile_name>")
                        print("Use /models to see available profiles.\n")
                    else:
                        try:
                            old_model = config.model
                            print(dim(f"Unloading {old_model}..."))
                            llm.unload_model()
                            config.switch_model(profile_key)
                            # Recreate LLM client with new config
                            llm = OllamaClient(config)
                            # Recreate agent with new LLM
                            agent = FactorioAgent(config, llm, tools)
                            print(green(f"Switched to {config.model}"))
                            print(f"Temperature: {config.temperature}, top_p: {config.top_p}, num_ctx: {config.num_ctx}\n")
                        except ValueError as e:
                            print(red(f"[ERROR] {e}\n"))

                elif cmd == "/switch":
                    print("Usage: /switch <profile_name>")
                    print("Use /models to see available profiles.\n")

                else:
                    print(f"Unknown command: {user_input}")
                    print("Type /help for available commands.\n")

                continue

            # Show thinking indicator
            print("Thinking...", end="", flush=True)

            try:
                # Get response from agent
                response = agent.chat(user_input)

                # Clear thinking indicator and show response
                print("\r" + " " * 20 + "\r", end="")
                print(format_response(response) + "\n")

            except Exception as e:
                print("\r" + " " * 20 + "\r", end="")

                # Check if it's a connection error, try reconnect
                error_str = str(e).lower()
                if "connection" in error_str or "rcon" in error_str or "socket" in error_str:
                    print(red("[ERROR] Connection lost. Attempting to reconnect..."))
                    if tools.reconnect(max_attempts=3, delay=2.0):
                        print(green("[OK] Reconnected! Please try your request again.\n"))
                    else:
                        print(red("[ERROR] Could not reconnect. Is Factorio still running?\n"))
                else:
                    print(red(f"[ERROR] {type(e).__name__}: {e}\n"))

    except KeyboardInterrupt:
        print("\n")

    # Cleanup
    print(dim("Unloading model..."))
    if llm.unload_model():
        print(dim("Model unloaded from GPU."))
    tools.disconnect()
    print("Goodbye!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
