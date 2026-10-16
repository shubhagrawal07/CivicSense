import argparse
import csv
import json
import math
import random
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = Path(__file__).resolve().parents[2]
CATEGORIES_FILE = ROOT / "shared" / "categories.json"
GOLD_FILE = ROOT / "ml" / "datasets" / "civic_text_v1.csv"
OUT_FILE = ROOT / "ml" / "datasets" / "civic_text_v2.csv"
WORK_DIR = ROOT / "ml" / "datasets" / "raw_v2"
MANIFEST_FILE = WORK_DIR / "manifest.json"
LOCAL_DIR = WORK_DIR / "local"

CLAUDE_MODEL = "claude-haiku-5-5"
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
SIMILARITY_LIMIT = 0.85

SUBCATEGORY_NOTES = {
    "pothole_single": "one pothole or crater in a road",
    "road_surface_broken": "a road surface that is worn, cracked, sunken or patchy",
    "lid_missing": "a manhole or drain chamber with no cover",
    "lid_broken": "a manhole cover that is cracked, loose, sunken or broken",
    "missed_collection": "garbage that was not collected on schedule",
    "bin_overflow": "public bins or containers overflowing",
    "illegal_dumping": "waste dumped or burnt in places it should not be",
    "light_off": "streetlights that are dead, off, or on at the wrong time",
    "light_flickering": "streetlights that flicker, blink or are very dim",
    "pole_damaged": "a streetlight pole that is bent, rusted, leaning or cracked",
    "pipe_leak": "a slow or steady leak in a water pipe, tap or valve",
    "pipe_burst": "a burst or broken water main spraying water",
    "power_cut": "no electricity, repeated cuts, or voltage trouble",
    "exposed_wire": "loose, hanging, sparking or exposed electric wires and boxes",
    "transformer_issue": "a transformer that sparks, smokes, leaks oil or has failed",
    "drain_blocked": "a drain or gutter that is clogged and overflowing",
    "sewage_overflow": "sewage coming up or flowing where it should not",
    "waterlogging": "rainwater standing on roads or in underpasses",
    "footpath": "broken, missing or uneven footpath tiles, kerbs or ramps",
    "railing_or_divider": "damaged railings, dividers, barriers or guard rails",
    "public_furniture": "broken benches, bus shelters, toilets, swings or park items",
    "signage": "fallen, bent or unreadable signs and boards",
    "fallen_tree": "a fallen tree or heavy branches on or near the road",
    "debris": "rubble, building material or junk left on the road",
    "other": (
        "complaints that fit none of the other nine categories: noise, stray "
        "animals, parking, hawkers, pollution, queries about services, thanks, "
        "follow-ups with no detail, or messages too vague to classify"
    ),
}

STYLES = [
    "angry and frustrated",
    "polite and formal",
    "short and blunt, like a text message",
    "long-winded, with extra background",
    "an elderly person using simple words",
    "typed in a hurry with typos and little punctuation",
    "neutral and factual, like a field report",
    "worried about children or safety",
]
LENGTHS = [
    "3 to 6 words",
    "one short sentence",
    "one or two sentences",
    "two or three sentences with concrete details",
]
LANGUAGES = [
    "plain English",
    "plain English",
    "English mixed with Hindi words written in roman script",
    "Hindi written in roman script",
]
PLACES = [
    "most of them name a landmark, area or street",
    "none of them mention any location",
    "about half of them mention a location",
]

SYSTEM_PROMPT = (
    "You write sample messages that citizens in Indian cities send to a civic "
    "complaint app. They are used as training data for a text classifier, so "
    "they must read like real people wrote them and differ from one another in "
    "wording, details and structure."
)

# a small local model needs shorter lists and more spare rows
BACKEND_DEFAULTS = {
    "claude": {"per_request": 25, "overshoot": 1.4},
    "ollama": {"per_request": 15, "overshoot": 1.6},
}


def load_taxonomy():
    data = json.loads(CATEGORIES_FILE.read_text())
    return data["categories"]


def build_prompt(label, sub_key, style, length, language, places, other_labels, n):
    note = SUBCATEGORY_NOTES[sub_key]
    lines = [
        f"Write {n} different complaint messages.",
        f"Topic: {label} - {note}.",
        f"Tone: {style}.",
        f"Length: {length}.",
        f"Language: {language}.",
        f"Location: {places}.",
        "",
        (
            "Output one message per line. No numbering, no bullets, no quotes, "
            "no blank lines and nothing else. Vary the situation, the objects "
            "mentioned and the opening words, and do not reuse a sentence pattern."
        ),
    ]
    if sub_key == "other":
        lines.append(
            "None of the messages may be about: " + ", ".join(other_labels) + "."
        )
    return "\n".join(lines)


def plan_requests(per_class, seed, per_request, overshoot):
    rng = random.Random(seed)
    cats = load_taxonomy()
    labels = {c["key"]: c["label"] for c in cats}
    per_cat = math.ceil(per_class * overshoot / per_request)
    plan = []
    for cat in cats:
        subs = [s["key"] for s in cat["subcategories"]] or ["other"]
        others = [v for k, v in labels.items() if k != cat["key"]]
        for n in range(per_cat):
            sub = subs[n % len(subs)]
            spec = {
                "id": f"r{len(plan):04d}",
                "category": cat["key"],
                "subcategory": "" if cat["key"] == "other" else sub,
                "style": rng.choice(STYLES),
                "length": rng.choice(LENGTHS),
                "language": rng.choice(LANGUAGES),
                "places": rng.choice(PLACES),
            }
            spec["prompt"] = build_prompt(
                cat["label"],
                sub,
                spec["style"],
                spec["length"],
                spec["language"],
                spec["places"],
                others,
                per_request,
            )
            plan.append(spec)
    return plan


def make_plan(args, backend):
    defaults = BACKEND_DEFAULTS[backend]
    per_request = args.per_request or defaults["per_request"]
    overshoot = args.overshoot or defaults["overshoot"]
    return plan_requests(args.per_class, args.seed, per_request, overshoot)


def save_manifest(backend, model, args, plan):
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(
        json.dumps(
            {
                "backend": backend,
                "model": model,
                "created": time.strftime("%Y-%m-%d"),
                "per_class": args.per_class,
                "batch_id": None,
                "requests": plan,
            },
            indent=1,
        )
    )


def show_dry_run(plan):
    print(f"{len(plan)} requests")
    for spec in plan[:2] + plan[-1:]:
        print("---", spec["id"], spec["category"], spec["subcategory"])
        print(spec["prompt"])


def submit_claude(args):
    import anthropic
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    plan = make_plan(args, "claude")
    if args.dry_run:
        show_dry_run(plan)
        return
    client = anthropic.Anthropic()
    requests = [
        Request(
            custom_id=spec["id"],
            params=MessageCreateParamsNonStreaming(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                output_config={"effort": "low"},
                messages=[{"role": "user", "content": spec["prompt"]}],
            ),
        )
        for spec in plan
    ]
    batch = client.messages.batches.create(requests=requests)
    save_manifest("claude", CLAUDE_MODEL, args, plan)
    manifest = json.loads(MANIFEST_FILE.read_text())
    manifest["batch_id"] = batch.id
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=1))
    print("batch", batch.id, "submitted,", len(plan), "requests")


def ask_ollama(model, prompt, temperature):
    body = json.dumps(
        {
            "model": model,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": 1500},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        }
    ).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.load(resp)["message"]["content"]


def check_ollama(model):
    try:
        with urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=10) as resp:
            installed = [m["name"] for m in json.load(resp)["models"]]
    except (urllib.error.URLError, OSError) as err:
        raise SystemExit(
            f"cannot reach Ollama at {OLLAMA_TAGS_URL} ({err}). Start it with "
            "`ollama serve` or open the Ollama app."
        )
    if model not in installed and f"{model}:latest" not in installed:
        raise SystemExit(f"model {model} is not installed, run `ollama pull {model}`")


def same_plan_as_saved(plan):
    if not MANIFEST_FILE.exists():
        return True
    saved = json.loads(MANIFEST_FILE.read_text())
    old = {r["id"]: r["prompt"] for r in saved["requests"]}
    return all(old.get(spec["id"]) == spec["prompt"] for spec in plan)


def run_ollama(args):
    plan = make_plan(args, "ollama")
    if args.dry_run:
        show_dry_run(plan)
        return
    check_ollama(args.model)
    has_replies = LOCAL_DIR.exists() and any(LOCAL_DIR.glob("r*.txt"))
    if has_replies and not same_plan_as_saved(plan):
        raise SystemExit(
            "saved replies in raw_v2/local were made from a different plan "
            "(other --per-class, --seed or --per-request). Delete that folder "
            "to start over, or rerun with the old options."
        )
    save_manifest("ollama", args.model, args, plan)
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    todo = [s for s in plan if not (LOCAL_DIR / f"{s['id']}.txt").exists()]
    print(f"{len(plan) - len(todo)} done already, {len(todo)} to go")
    failed = 0
    for i, spec in enumerate(todo, start=1):
        try:
            text = ask_ollama(args.model, spec["prompt"], args.temperature)
        except (urllib.error.URLError, OSError, KeyError, ValueError) as err:
            failed += 1
            print(f"{spec['id']} failed: {err}")
            if failed >= 5:
                raise SystemExit("too many failures in a row, stopping")
            continue
        failed = 0
        (LOCAL_DIR / f"{spec['id']}.txt").write_text(text)
        if i % 10 == 0:
            print(f"{i}/{len(todo)}")


SKIP_LINE = re.compile(r"^(here are|here is|sure|okay|certainly)\b", re.IGNORECASE)


def clean_line(line):
    line = line.strip()
    line = re.sub(r"^(\d+[.)]|[-*•])\s+", "", line)
    return line.strip().strip("\"'").strip()


def parse_messages(text):
    out = []
    for line in text.splitlines():
        line = clean_line(line)
        if line.endswith(":") or SKIP_LINE.match(line):
            continue
        if 2 <= len(line) <= 300:
            out.append(line)
    return out


def rows_from_claude(manifest):
    import anthropic

    client = anthropic.Anthropic()
    batch = client.messages.batches.retrieve(manifest["batch_id"])
    if batch.processing_status != "ended":
        raise SystemExit(f"batch not finished: {batch.processing_status}")
    specs = {s["id"]: s for s in manifest["requests"]}
    rows = []
    failed = 0
    for item in client.messages.batches.results(manifest["batch_id"]):
        if item.result.type != "succeeded":
            failed += 1
            continue
        msg = item.result.message
        text = "".join(b.text for b in msg.content if b.type == "text")
        spec = specs[item.custom_id]
        for line in parse_messages(text):
            rows.append((spec["category"], spec["subcategory"], line))
    print(f"{failed} failed requests")
    return rows


def rows_from_ollama(manifest):
    rows = []
    missing = 0
    for spec in manifest["requests"]:
        path = LOCAL_DIR / f"{spec['id']}.txt"
        if not path.exists():
            missing += 1
            continue
        for line in parse_messages(path.read_text()):
            rows.append((spec["category"], spec["subcategory"], line))
    print(f"{missing} requests not generated yet")
    return rows


def norm(text):
    return re.sub(r"[^a-z0-9 ]+", "", text.lower()).strip()


def dedupe(rows, gold_texts):
    seen = {norm(t) for t in gold_texts}
    exact = []
    for cat, sub, text in rows:
        key = norm(text)
        if key and key not in seen:
            seen.add(key)
            exact.append((cat, sub, text))

    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
    vec.fit([t for _, _, t in exact] + list(gold_texts))
    gold_m = vec.transform(gold_texts)

    kept = []
    by_cat = {}
    for row in exact:
        by_cat.setdefault(row[0], []).append(row)
    for items in by_cat.values():
        m = vec.transform([t for _, _, t in items])
        near_gold = (m @ gold_m.T).max(axis=1).toarray().ravel()
        sims = m @ m.T
        chosen = []
        for i, row in enumerate(items):
            if near_gold[i] >= SIMILARITY_LIMIT:
                continue
            if chosen and sims[i, chosen].max() >= SIMILARITY_LIMIT:
                continue
            chosen.append(i)
            kept.append(row)
    return kept


def balance(rows, per_class, seed):
    rng = random.Random(seed)
    by_cat = {}
    for row in rows:
        by_cat.setdefault(row[0], []).append(row)
    out = []
    for cat, items in sorted(by_cat.items()):
        rng.shuffle(items)
        short = max(0, per_class - len(items))
        note = f", short by {short}" if short else ""
        print(f"{cat}: {len(items)} after dedupe{note}")
        out.extend(items[:per_class])
    return out


def collect(args):
    manifest = json.loads(MANIFEST_FILE.read_text())
    if manifest["backend"] == "ollama":
        rows = rows_from_ollama(manifest)
    else:
        rows = rows_from_claude(manifest)
    print(f"{len(rows)} raw messages")
    gold = [r["text"] for r in csv.DictReader(GOLD_FILE.open(newline=""))]
    rows = dedupe(rows, gold)
    rows = balance(rows, manifest["per_class"], args.seed)
    random.Random(args.seed).shuffle(rows)
    with OUT_FILE.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "text", "category", "subcategory", "source", "split"])
        for i, (cat, sub, text) in enumerate(rows, start=1):
            w.writerow([f"g{i:05d}", text, cat, sub, manifest["backend"], "train"])
    print(f"wrote {len(rows)} rows to {OUT_FILE}")


def add_plan_options(p):
    p.add_argument("--per-class", type=int, default=1000)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--per-request", type=int)
    p.add_argument("--overshoot", type=float)
    p.add_argument("--dry-run", action="store_true")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("submit", help="send a Claude batch")
    add_plan_options(p)
    p.set_defaults(func=submit_claude)

    p = sub.add_parser("run-local", help="generate with a local Ollama model")
    add_plan_options(p)
    p.add_argument("--model", default="llama3.2:3b")
    p.add_argument("--temperature", type=float, default=0.9)
    p.set_defaults(func=run_ollama)

    p = sub.add_parser("collect")
    p.add_argument("--seed", type=int, default=7)
    p.set_defaults(func=collect)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
