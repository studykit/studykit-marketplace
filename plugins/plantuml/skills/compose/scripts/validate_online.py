"""Validate PlantUML syntax using the PlantUML online server API.

Usage:
    uv run skills/compose/scripts/validate_online.py <file.puml> [file2.puml ...]
    echo '@startuml\nA -> B\n@enduml' | uv run skills/compose/scripts/validate_online.py -

No local PlantUML installation required.
"""

import sys
import zlib
import urllib.request
import urllib.error
import json
from pathlib import Path

PLANTUML_SERVER = "https://www.plantuml.com/plantuml"


def _encode_plantuml(text: str) -> str:
    """Encode PlantUML text using the PlantUML deflate encoding."""
    compressed = zlib.compress(text.encode("utf-8"))[2:-4]
    return _encode64(compressed)


def _encode64(data: bytes) -> str:
    """PlantUML's custom base64 encoding."""
    res = []
    for i in range(0, len(data), 3):
        if i + 2 < len(data):
            b1, b2, b3 = data[i], data[i + 1], data[i + 2]
        elif i + 1 < len(data):
            b1, b2, b3 = data[i], data[i + 1], 0
        else:
            b1, b2, b3 = data[i], 0, 0

        res.append(_encode6bit(b1 >> 2))
        res.append(_encode6bit(((b1 & 0x3) << 4) | (b2 >> 4)))
        res.append(_encode6bit(((b2 & 0xF) << 2) | (b3 >> 6)))
        res.append(_encode6bit(b3 & 0x3F))
    return "".join(res)


def _encode6bit(b: int) -> str:
    if b < 10:
        return chr(48 + b)
    b -= 10
    if b < 26:
        return chr(65 + b)
    b -= 26
    if b < 26:
        return chr(97 + b)
    b -= 26
    if b == 0:
        return "-"
    if b == 1:
        return "_"
    return "?"


def validate(text: str) -> tuple[bool, str]:
    """Validate PlantUML text via the online server.

    Returns (is_valid, message).
    """
    encoded = _encode_plantuml(text)
    url = f"{PLANTUML_SERVER}/map/{encoded}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            if "Error" in body or "Syntax Error" in body:
                return False, body.strip()
            return True, "OK"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return False, f"Connection error: {e.reason}"


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.puml> [file2.puml ...]")
        print(f"       echo '...' | {sys.argv[0]} -")
        sys.exit(1)

    files = sys.argv[1:]
    errors = 0

    for filepath in files:
        if filepath == "-":
            text = sys.stdin.read()
            label = "<stdin>"
        else:
            p = Path(filepath)
            if not p.exists():
                print(f"SKIP: {filepath} (file not found)")
                continue
            text = p.read_text(encoding="utf-8")
            label = filepath

        print(f"Checking {label} ... ", end="", flush=True)
        valid, msg = validate(text)
        if valid:
            print("OK")
        else:
            print("FAIL")
            print(f"  {msg}")
            errors += 1

    print()
    if errors > 0:
        print(f"{errors} file(s) with errors")
        sys.exit(1)
    else:
        print("All files valid")


if __name__ == "__main__":
    main()
