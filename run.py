#!/usr/bin/env python3
"""Vision bake-off runner.

Judges every image in frames/** with two calls per image:
  1. strict QC prompt (STYLE/CONTENT/DEFECTS/verdict)
  2. known-answer yes/no probe (ground truth: is the ghost girl's face visible?)

Writes one JSON row per call to --out. OpenAI-compatible endpoint (default: Venice).

Usage:
  export VENICE_API_KEY=...
  python3 run.py --model qwen-3-8-27b --out results/qwen-3-8-27b.jsonl
"""
import argparse
import base64
import json
import mimetypes
import os
import pathlib
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

API = os.environ.get("VISION_BENCH_API", "https://api.venice.ai/api/v1/chat/completions")
KEY = os.environ.get("VENICE_API_KEY", "")
TIMEOUT = int(os.environ.get("VISION_BENCH_TIMEOUT", "120"))
MAX_TOKENS = 400

QC_PROMPT = (
    "Judge this film still strictly. Intended style: {style}. Intended content: {content}. "
    "Answer in max 5 short lines: STYLE (does it truly read as the intended style?) score/10; "
    "CONTENT (which intended elements are present/missing/wrong) score/10; "
    "DEFECTS (anatomy, extra limbs/faces, text, merged bodies) or none; one-line verdict."
)
KNOWN_PROMPT = (
    "Answer with exactly one word, yes or no: is the ghost girl's face visible "
    "(eyes, nose or mouth showing through the hair)?"
)

STYLE_OF = {"stopmotion": "Laika-style stop-motion animation still",
            "anime": "2D anime film still, Makoto Shinkai adjacent"}
CONTENT_OF = {
    "crawl": ("a ghost girl with long wet black hair over her face crawling OUT of a CRT TV, "
              "half her body still inside the screen; three kids on a couch: a white girl screaming, "
              "a Black boy leaping over the couch arm to flee, an Asian boy fainting backward"),
    "sheet": ("a 10-year-old ghost girl, very long straight wet black hair completely covering her face, "
              "pale skin, soaked white nightdress, barefoot; front, three-quarter and back views; "
              "the same character in each view"),
}


def data_uri(path: pathlib.Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def call(model: str, image: pathlib.Path, prompt: str, kind: str) -> dict:
    body = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "temperature": 0,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_uri(image)}},
        ]}],
    }
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    )
    t0 = time.time()
    row = {"model": model, "image": str(image), "kind": kind}
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            payload = json.load(r)
        row["latency_s"] = round(time.time() - t0, 2)
        row["response"] = payload["choices"][0]["message"]["content"]
        usage = payload.get("usage", {})
        row["tokens_in"] = usage.get("prompt_tokens")
        row["tokens_out"] = usage.get("completion_tokens")
    except Exception as e:  # noqa: BLE001 - record, don't abort the sweep
        row["latency_s"] = round(time.time() - t0, 2)
        row["error"] = f"{type(e).__name__}: {e}"
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", default="frames")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    if not KEY:
        print("VENICE_API_KEY not set", file=sys.stderr)
        return 2

    images = sorted(p for p in pathlib.Path(args.frames).rglob("*")
                    if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"))
    if not images:
        print(f"no images under {args.frames}", file=sys.stderr)
        return 2

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    jobs = []
    for img in images:
        style = STYLE_OF.get(img.parent.name, img.parent.name)
        content = CONTENT_OF.get(img.parent.parent.name, img.parent.parent.name)
        jobs.append((img, QC_PROMPT.format(style=style, content=content), "qc"))
        jobs.append((img, KNOWN_PROMPT, "known"))

    with out.open("w") as fh, ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(call, args.model, img, prompt, kind) for img, prompt, kind in jobs]
        for fut in futures:
            row = fut.result()
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            print(f"{row['image']} {row['kind']} {row.get('latency_s')}s "
                  f"{'ERR' if 'error' in row else 'ok'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
