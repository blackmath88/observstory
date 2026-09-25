#!/usr/bin/env python3
"""Entry point. With no arguments it runs `build` (what the GitHub Action calls)."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from observstory.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
