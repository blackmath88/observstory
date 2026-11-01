"""Observatory — Project Memory page: one self-contained HTML file around an observstory.memory-ui/v1 bundle.

Static mode embeds the bundle (safe for GitHub Pages: no tokens, no write path). Live mode (data-live) is the
same page served by a host that also answers GET api/bundle and POST api/context."""

from __future__ import annotations

import html
import json
import pathlib

ASSETS = pathlib.Path(__file__).resolve().parent / "assets" / "memory"


def _embed_json(obj) -> str:
    # inside <script type="application/json">: neutralise anything that could close the element
    return json.dumps(obj, ensure_ascii=False, sort_keys=True).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def render_memory(bundle: dict, *, live: bool = False, api: str = "api/") -> str:
    css = (ASSETS / "app.css").read_text(encoding="utf-8")
    js = (ASSETS / "app.js").read_text(encoding="utf-8")
    mark = (ASSETS / "observatory-parked.svg").read_text(encoding="utf-8")
    mark_lit = (ASSETS / "observatory-parked-lit.svg").read_text(encoding="utf-8")
    title = f"Project Memory · {bundle.get('repository', '')}"
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{html.escape(title)}</title>"
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; "
        "script-src 'unsafe-inline'; img-src data:; connect-src 'self'; base-uri 'none'; form-action 'none'\">"
        f"<style>{css}</style></head><body>"
        f"<div id=\"app\" data-live=\"{'1' if live else '0'}\" data-api=\"{html.escape(api)}\"></div>"
        f"<template id=\"mark\">{mark}</template><template id=\"mark-lit\">{mark_lit}</template>"
        f"<script type=\"application/json\" id=\"bundle\">{_embed_json(bundle)}</script>"
        f"<noscript>This page needs JavaScript to present the recorded memory. The same data is in the JSON export.</noscript>"
        f"<script>{js}</script></body></html>\n"
    )
