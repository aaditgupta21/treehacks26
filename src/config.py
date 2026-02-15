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
    """Load raw API keys. Use load_poke_api_keys_with_names() for (name, key) pairs."""
    return [k for _, k in load_poke_api_keys_with_names()]


def load_poke_api_keys_with_names() -> list[tuple[str, str]]:
    """
    Load (name, key) from poke_api_keys.txt.
    Format: name:key (e.g. Aadit:eyJ..., armaan:eyJ...) — use "Aadit", "Armaan" for frontend display.
    Returns list of (name, key). Name is capitalized for display.
    """
    f = _find_api_keys_file()
    if not f.exists():
        return []
    out = []
    for line in f.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            name, key = line.split(":", 1)
            name = name.strip()
            key = key.strip()
        else:
            name = "Teammate"
            key = line
        if len(key) > 20 and (key.startswith("pk_") or key.startswith("eyJ")):
            # Capitalize name for display (me -> Me, armaan -> Armaan)
            name = name.strip().capitalize() if name else "Teammate"
            out.append((name, key))
    return out
