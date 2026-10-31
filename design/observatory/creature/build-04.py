#!/usr/bin/env python3
"""Inline the pixel frames into study-04.html (self-contained artifact body).

    python3 design/observatory/creature/build-04.py

Frames in frames/ come from rig/README steps: resize the owner's Nano Banana images to 320x179,
quantise them to one shared 64-colour palette, and cut the creature with rig/mask.mjs."""
import base64, pathlib
here = pathlib.Path(__file__).parent
uri = lambda p: "data:image/png;base64," + base64.b64encode((here / "frames" / p).read_bytes()).decode()
t = (here / "study-04.src.html").read_text()
for key, f in {"%%Q17%%": "up.png", "%%Q18%%": "rest.png", "%%CUTUP%%": "cut-up.png", "%%CUTREST%%": "cut-rest.png"}.items():
    t = t.replace(key, uri(f))
(here / "study-04.html").write_text(t)
print("built study-04.html")
