"""
fix_mojibake.py — Repairs a specific double-encoding corruption found in
several frontend JS files: correct UTF-8 emoji got decoded with a "WHATWG
windows-1252" decoder (the one browsers/JS environments use) instead of
UTF-8, then re-saved as UTF-8.

This is NOT the same as Python's standard `cp1252` codec. WHATWG windows-1252
maps all 256 byte values to something, including 5 bytes Python's strict
cp1252 leaves undefined (0x81, 0x8D, 0x8F, 0x90, 0x9D) — WHATWG passes those
through as their raw C1 control-code identity instead of erasing them. That's
why a plain `.encode('cp1252')` reversal fails partway through these files.

Generated with qwen2.5-coder:7b via Ollama MCP, assembled and bug-fixed by
Claude (the draft called fix_file() twice per path — once in the if, again
in the elif — double-processing and double-writing every file, and its
bool-only return couldn't actually distinguish "skipped" from "unchanged"
the way the summary claimed to).
"""
from __future__ import annotations
import sys

WHATWG_GAP_BYTES = {0x81, 0x8D, 0x8F, 0x90, 0x9D}


def whatwg_1252_to_bytes(text: str) -> bytes:
    result = bytearray()
    for ch in text:
        cp = ord(ch)
        if cp in WHATWG_GAP_BYTES:
            result.append(cp)
            continue
        try:
            result.extend(ch.encode("cp1252"))
        except UnicodeEncodeError:
            raise ValueError(f"character {ch!r} (U+{cp:04X}) is not mojibake — aborting this file")
    return bytes(result)


def fix_file(path: str) -> str:
    with open(path, "r", encoding="utf-8-sig") as f:
        original = f.read()

    try:
        repaired = whatwg_1252_to_bytes(original).decode("utf-8")
    except ValueError as e:
        print(f"SKIP {path}: {e}", file=sys.stderr)
        return "skipped"

    if repaired == original:
        print(f"OK   {path}: no changes needed")
        return "unchanged"

    with open(path, "w", encoding="utf-8") as f:
        f.write(repaired)
    print(f"FIXED {path}: {len(original) - len(repaired)} fewer characters after repair")
    return "fixed"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_mojibake.py <file1> [file2 ...]", file=sys.stderr)
        sys.exit(1)

    counts = {"fixed": 0, "unchanged": 0, "skipped": 0}
    for path in sys.argv[1:]:
        counts[fix_file(path)] += 1

    print(f"Summary: fixed {counts['fixed']}, unchanged {counts['unchanged']}, skipped {counts['skipped']}")
