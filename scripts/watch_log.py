"""
Live Factorio log viewer.

Usage:
    conda activate factorio
    python scripts/watch_log.py
"""

import os
import time

LOG_PATH = os.path.expandvars(r"%APPDATA%\Factorio\factorio-current.log")
LINES = 40
REFRESH = 2  # seconds


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def tail(filepath, n):
    """Get last n lines of file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            return lines[-n:] if len(lines) > n else lines
    except FileNotFoundError:
        return ["Log file not found: " + filepath]


def main():
    print(f"Watching: {LOG_PATH}")
    print(f"Showing last {LINES} lines, refresh every {REFRESH}s")
    print("Press Ctrl+C to stop\n")
    time.sleep(2)

    try:
        while True:
            clear()
            print("=" * 70)
            print(f"FACTORIO LOG - Last {LINES} lines (Ctrl+C to stop)")
            print("=" * 70)
            print()

            lines = tail(LOG_PATH, LINES)
            for line in lines:
                # Highlight important lines
                text = line.rstrip()
                if 'RCON' in text:
                    print(f">>> {text} <<<")
                elif 'Error' in text or 'error' in text:
                    print(f"!!! {text}")
                else:
                    print(text)

            time.sleep(REFRESH)

    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == '__main__':
    main()
