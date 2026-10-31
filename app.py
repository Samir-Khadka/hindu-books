"""Hindu Books — free scripture library (bilingual EN/NE).

Run: uvicorn app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

BASE = Path(__file__).parent
app = FastAPI(title="Hindu Books")
templates = Jinja2Templates(directory=str(BASE / "templates"))

PALETTE = {"bg": "#FAF6ED", "ink": "#2b2b2b", "violet": "#4c1d95",
           "gold": "#b8860b"}


def _load(name):
    return json.loads((BASE / "data" / f"{name}.json").read_text(
        encoding="utf-8"))


def _lang(request: Request) -> str:
    return "ne" if request.query_params.get("lang") == "ne" else "en"


def _t(obj: dict, lang: str, key: str) -> str:
    # title_en / title_ne / title_sa
    return obj.get(f"{key}_{lang}") or obj.get(f"{key}_en") or ""


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    lang = _lang(request)
    library = _load("library")
    return templates.TemplateResponse(request, "home.html", {
        "request": request, "lang": lang, "library": library,
        "t": _t ,
    })


@app.get("/book/{book_id}", response_class=HTMLResponse)
def book(request: Request, book_id: str):
    lang = _lang(request)
    try:
        book = _load(book_id)
    except FileNotFoundError:
        return HTMLResponse("<p>Not found.</p>", status_code=404)
    return templates.TemplateResponse(request, "book.html", {
        "request": request, "lang": lang, "book": book,
        "t": _t ,
    })


@app.get("/book/{book_id}/chapter/{n}", response_class=HTMLResponse)
def chapter(request: Request, book_id: str, n: int):
    lang = _lang(request)
    try:
        book = _load(book_id)
    except FileNotFoundError:
        return HTMLResponse("<p>Not found.</p>", status_code=404)
    chapters = book.get("chapters", [])
    ch = next((c for c in chapters if c["n"] == n), None)
    if not ch:
        return HTMLResponse("<p>Not found.</p>", status_code=404)
    prev_n = n - 1 if n > 1 else None
    next_n = n + 1 if n < len(chapters) else None
    return templates.TemplateResponse(request, "chapter.html", {
        "request": request, "lang": lang, "book": book, "ch": ch,
        "t": _t , "prev_n": prev_n, "next_n": next_n,
    })


@app.get("/search", response_class=HTMLResponse)
def search(request: Request, q: str = ""):
    lang = _lang(request)
    results = []
    if q.strip():
        ql = q.strip().lower()
        for entry in _load("library"):
            if entry.get("status") != "complete":
                continue
            try:
                book = _load(entry["id"])
            except FileNotFoundError:
                continue
            for ch in book.get("chapters", []):
                hay = " ".join([
                    ch.get("title_en", ""), ch.get("title_ne", ""),
                    ch.get("summary_en", ""), ch.get("summary_ne", ""),
                ]).lower()
                if ql in hay:
                    results.append({"book": book, "ch": ch})
                for v in ch.get("key_verses", []):
                    vhay = " ".join([v.get("en", ""), v.get("ne", ""),
                                     v.get("sa", "")]).lower()
                    if ql in vhay:
                        results.append({"book": book, "ch": ch,
                                        "verse": v})
                        break
    return templates.TemplateResponse(request, "search.html", {
        "request": request, "lang": lang, "q": q, "results": results,
        "t": _t ,
    })
