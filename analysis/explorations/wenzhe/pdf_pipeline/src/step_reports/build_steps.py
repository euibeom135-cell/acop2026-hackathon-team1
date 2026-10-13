"""Rebuild every report page from pdf_pipeline/results (read-only; nothing is recomputed or re-scored).
Run (from /Users/wma/Codes/DM1):  .venv/bin/python -W ignore pdf_pipeline/src/step_reports/build_steps.py [step1 .. step6 | index | summary | check]   (no argument = everything + link check)."""
import sys, importlib, re, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from base import *

def build_index():
    cards = "".join(f'<li><a href="{f}"><b>Step {n}: {t}</b></a> &ndash; {d}</li>' for n, t, f, d in STEPS)
    h = (f"<!doctype html><html><head><meta charset=utf-8><title>DM1 six-step pipeline</title>{CSS}</head><body style='--c:{PUR}'>{strip(-1)}<h1 style='color:{PUR}'>DM1 six-step pipeline (kickoff-faithful)</h1>"
         f"{box('Understand, split / cross-validate, preprocess, select, train, evaluate. Steps 1-5 use training rows only; Step 6 reads the single locked test scoring. Simulated data.')}<ol>{cards}</ol>"
         f"<p><a href='../summary.html'><b>Executive summary</b></a> (signal covariates, covariate vs ML, caveats) &middot; <a href='../../notes/compute_notes.html'>compute notes</a></p>"
         f"<p class=note>Rebuild: <code>.venv/bin/python -W ignore pdf_pipeline/src/step_reports/build_steps.py</code> from /Users/wma/Codes/DM1.</p><p class=foot>{FOOTER}</p></body></html>")
    (OUT / "index.html").write_text(h)

def check_links():
    bad = []; pages = list(OUT.glob("*.html")) + [REP / "summary.html"]
    for p in pages:
        t = p.read_text()
        for m in re.findall(r'(?:href|src)="([^"#]+)', t):
            if m.startswith(("http", "data:")): continue
            if not (p.parent / m).resolve().exists(): bad.append((p.name, m))
        if re.search(r"\bnan\b|\bNaN\b", re.sub(r"<style.*?</style>", "", t, flags=re.S)): bad.append((p.name, "NaN text"))
        if "<td></td>" in t: bad.append((p.name, "empty table cell"))
    print("LINK/FIG/NaN CHECK:", "OK" if not bad else bad); return bad

def main(args):
    want = args or ["step1", "step2", "step3", "step4", "step5", "step6", "index", "summary", "check"]
    for w in want:
        t = time.time()
        if w == "index": build_index()
        elif w == "check": check_links()
        else: importlib.import_module({"summary": "summary"}.get(w, w)).build()
        print("built", w, f"{time.time() - t:.1f}s", flush=True)
if __name__ == "__main__": main(sys.argv[1:])
