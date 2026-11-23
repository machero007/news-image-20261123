#!/usr/bin/env python3
"""Copy the bundled entry.png to /output/entry.png.

Stdlib only. Deterministic: the output bytes are exactly the bundled
entry.png, so repeated runs write identical bytes.
Run: python3 main.py
"""
import os

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1024 * 1024


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    out_dir = "/output"
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    with open(src, "rb") as f:
        data = f.read()
    if data[:8] != PNG_MAGIC:
        raise ValueError(f"{src} is not a PNG file (bad magic bytes)")
    if len(data) > MAX_BYTES:
        raise ValueError(f"{src} is {len(data)} bytes, over the {MAX_BYTES} byte limit")
    with open(dst, "wb") as f:
        f.write(data)
    print(f"wrote {dst} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
