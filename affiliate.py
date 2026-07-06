#!/usr/bin/env python3
"""affiliate.py — where does a new dot belong? Match its keywords against every
existing dot to (a) rank the project lanes it fits and (b) surface the dots it
should link to. Used by BOTH distill-session and ingest-source so a fresh dot
finds its home + neighbours instead of landing as an island.

Usage:
  affiliate.py --keywords "tweedie, sipm, gain" [--title "…"] [--top 8] [--dots DIR] [--json]

Dots dir resolves to: --dots, else $PALACE/dots, else ~/.claude/palace/dots.
Prints ranked lanes + candidate related dot ids (paste the best as `- related:: [[id]]`).
"""
import sys, os, re, json, glob
from pathlib import Path
from collections import defaultdict

STOP = set("the a an of to in for and or on with by is are be as at from into via using "
           "we our this that it its per over under new use used uses model method".split())

def tokens(s):
    return {w for w in re.findall(r"[a-z0-9][a-z0-9+/_.-]{1,}", (s or "").lower()) if w not in STOP}

def parse(path):
    t = path.read_text(encoding="utf-8", errors="replace")
    fm = {}
    m = re.match(r"^---\n(.*?)\n---", t, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith(" "):
                k, _, v = line.partition(":"); fm[k.strip()] = v.strip()
    kw = fm.get("keywords", "")
    kws = [x.strip().lower() for x in kw.strip("[]").split(",") if x.strip()] if kw else []
    return {"id": path.stem, "project": fm.get("project", "misc"),
            "title": fm.get("title", ""), "kw": set(kws)}

def resolve_dots(cli):
    for c in (cli, os.environ.get("PALACE") and os.path.join(os.environ["PALACE"], "dots"),
              os.path.expanduser("~/.claude/palace/dots")):
        if c and Path(c).is_dir() and glob.glob(os.path.join(c, "*.md")):
            return c
    raise SystemExit("no dots dir found — pass --dots /path/to/palace/dots")

def main():
    a = sys.argv[1:]; kw = ""; title = ""; top = 8; dots = None; asjson = False
    while a:
        x = a.pop(0)
        if x == "--keywords": kw = a.pop(0)
        elif x == "--title": title = a.pop(0)
        elif x == "--top": top = int(a.pop(0))
        elif x == "--dots": dots = a.pop(0)
        elif x == "--json": asjson = True
    qkw = {x.strip().lower() for x in kw.split(",") if x.strip()}
    qtok = qkw | tokens(title)
    if not qtok: raise SystemExit("give --keywords (and optionally --title)")

    ddir = resolve_dots(dots)
    scored = []
    for f in glob.glob(os.path.join(ddir, "*.md")):
        d = parse(Path(f))
        shared = qkw & d["kw"]                                   # exact keyword hits (strong)
        ttok = tokens(d["title"]) & qtok                          # title/keyword token overlap (weak)
        score = 3 * len(shared) + len(ttok - shared)
        if score: scored.append({**d, "score": score, "shared": sorted(shared | ttok)})
    scored.sort(key=lambda x: -x["score"])

    lanes = defaultdict(lambda: {"score": 0, "hits": 0})
    for s in scored:
        lanes[s["project"]]["score"] += s["score"]; lanes[s["project"]]["hits"] += 1
    ranked = sorted(({"project": p, **v} for p, v in lanes.items()), key=lambda x: -x["score"])
    related = [{"id": s["id"], "project": s["project"], "score": s["score"], "shared": s["shared"]}
               for s in scored[:top]]

    if asjson:
        print(json.dumps({"lanes": ranked, "related": related}, ensure_ascii=False, indent=1)); return
    print("query keywords:", ", ".join(sorted(qkw)) or "(none)")
    print("\nbest-fit lanes (project ← keyword overlap):")
    for r in ranked[:6]: print(f"  {r['score']:3d}  {r['project']:<22} ({r['hits']} dot hits)")
    if not ranked: print("  (no overlap — likely a NEW lane; pick a Scope:Subject)")
    print("\ncandidate related dots (paste the apt ones as `- related:: [[id]]`):")
    for r in related: print(f"  {r['score']:3d}  [[{r['id']}]]  ({r['project']}) — shared: {', '.join(r['shared'])}")

if __name__ == "__main__":
    main()
