"""Load Poke API keys from poke_api_keys.txt for calendar sync."""

from pathlib import Path

# Find project root: same directory as poke_api_keys.txt
def _find_api_keys_file() -> Path:
    # Try next to src/
    for base in [Path(__file__).resolve().parent.parent, Path.cwd()]:
        f = base / "poke_api_keys.txt"
        if f.exists():
            return f
    return Path.cwd() / "poke_api_keys.txt"


def load_poke_api_keys() -> list[str]:
    """
    Load all Poke API keys from poke_api_keys.txt.
    Returns raw keys (pk_xxx) - one per line. Skips comments and empty lines.
    """
    f = _find_api_keys_file()
    if not f.exists():
        return []
    keys = []
    for line in f.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Support name:pk_xxx or just pk_xxx
        if ":" in line:
            _, key = line.split(":", 1)
            key = key.strip()
        else:
            key = line
        # JWT (eyJ...) from poke login works; pk_ often returns 401
        if len(key) > 20 and (key.startswith("pk_") or key.startswith("eyJ")):
            keys.append(key)
    return keys
