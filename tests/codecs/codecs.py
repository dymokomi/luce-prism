#!/usr/bin/env python3
"""The codec driver against the pinned fixtures (usage: codecs.py CODEC SCRATCH [ORACLE]):
the inventory audit (every named legacy case has an executable Luce test), the foreign
codec fixtures, the text surface and the native encodings, each compared with SHA-256s
the C++ reference recorded. An optional C++ oracle built against kinogaki-core also
cross-checks them."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compatibility.oracle import run_codecs, run_surface, run_native  # noqa: E402
from compatibility.coverage import audit  # noqa: E402

if __name__ == "__main__":
    codec, scratch = Path(sys.argv[1]), Path(sys.argv[2])
    oracle = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else None
    audit(require_complete=True)
    run_codecs(codec, oracle, scratch)
    run_surface(codec, oracle, scratch)
    run_native(codec, oracle, scratch)
