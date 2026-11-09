#!/usr/bin/env python3
"""
evidence_pipeline.py — Evidence Analysis Pipeline (Project Extensions 2 & 3).

Combines two layers:
  P2  Deterministic completeness check — scans an evidence folder, links each
      document to the controls it supports (keyword + filename rules), and flags
      every expected control as PRESENT / STALE / MISSING with a completeness score.
  P3  AI-assisted analysis — for each document, drafts a summary, suggested
      controls, and potential gaps (mock offline mode by default; real Anthropic
      API when ANTHROPIC_API_KEY is set). Every AI output is labelled
      PENDING_HUMAN_REVIEW — the human control owner is accountable.

Outputs (to ../output/):
  evidence_report.md        — full human-readable report (P2 + P3)
  evidence_matrix.csv       — control × status × matched files × freshness
  evidence_ai_suggestions.csv — per-document AI suggestions for human sign-off
  evidence_completeness.png — completeness by CSF function

Usage:
  python evidence_pipeline.py [--evidence ../evidence] [--outdir ../output]
                              [--ai-mode auto|mock|real] [--today YYYY-MM-DD]
"""
from __future__ import annotations
import argparse, csv, os, re, sys, datetime as dt
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from csf_data import FUNCTIONS, CATEGORIES
from evidence_rules import EVIDENCE_RULES
from ai_analyst import analyze_document, active_mode

DATE_RE = re.compile(r"(20\d{2})-(\d{2})-(\d{2})")
TEXT_EXT = {".txt", ".md", ".csv", ".log", ".json", ".yaml", ".yml"}


# ---------- reading evidence ------------------------------------------------
def read_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext in TEXT_EXT:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        if ext == ".pdf":
            try:
                import pypdf
                r = pypdf.PdfReader(path)
                return "\n".join((pg.extract_text() or "") for pg in r.pages)
            except Exception:
                return ""
        if ext == ".docx":
            try:
                import docx
                return "\n".join(p.text for p in docx.Document(path).paragraphs)
            except Exception:
                return ""
    except Exception:
        return ""
    return ""


def evidence_date(text: str, path: str, today: dt.date) -> dt.date:
    """Prefer an in-document date (most recent, not in the future); else file mtime."""
    dates = []
    for y, m, d in DATE_RE.findall(text):
        try:
            cand = dt.date(int(y), int(m), int(d))
            if cand <= today:
                dates.append(cand)
        except ValueError:
            pass
    if dates:
        return max(dates)
    return dt.date.fromtimestamp(os.path.getmtime(path))


# ---------- P2: deterministic matching & scoring ----------------------------
def scan_evidence(evidence_dir: str, today: dt.date):
    files = []
    for name in sorted(os.listdir(evidence_dir)):
        p = os.path.join(evidence_dir, name)
        if not os.path.isfile(p):
            continue
        text = read_text(p)
        files.append({"name": name, "path": p, "text": text,
                      "date": evidence_date(text, p, today)})
    return files


def match(files, today: dt.date):
    """For each rule, find matching files and compute status."""
    results = []
    for r in EVIDENCE_RULES:
        matched = []
        for fobj in files:
            low = fobj["text"].lower()
            kw = [k for k in r["keywords"] if k in low]
            fn = any(h in fobj["name"].lower() for h in r["filename_hints"])
            if kw or fn:
                matched.append({"file": fobj["name"], "date": fobj["date"],
                                "why": (f"keyword: {kw[0]}" if kw else "filename match")})
        if not matched:
            status, score = "MISSING", 0.0
            newest = None
        else:
            newest = max(m["date"] for m in matched)
            age = (today - newest).days
            if age > r["freshness_days"]:
                status, score = "STALE", 0.5
            else:
                status, score = "PRESENT", 1.0
        results.append({**r, "matched": matched, "status": status,
                        "score": score, "newest": newest})
    return results


def summarise(results):
    by_func = defaultdict(lambda: {"score": 0.0, "n": 0, "present": 0, "stale": 0, "missing": 0})
    for r in results:
        f = r["csf"].split(".")[0]
        by_func[f]["score"] += r["score"]
        by_func[f]["n"] += 1
        by_func[f][r["status"].lower()] += 1
    overall = sum(r["score"] for r in results) / len(results)
    return by_func, overall


# ---------- charts ----------------------------------------------------------
def completeness_chart(by_func, path):
    order = [f for f in ["GV", "ID", "PR", "DE", "RS", "RC"] if f in by_func]
    pct = [by_func[f]["score"] / by_func[f]["n"] * 100 for f in order]
    colors = ["#548235" if p >= 80 else "#BF8F00" if p >= 50 else "#C0392B" for p in pct]
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    bars = ax.bar([FUNCTIONS[f] for f in order], pct, color=colors, width=0.6)
    ax.set_ylim(0, 100); ax.set_ylabel("Evidence completeness (%)")
    ax.set_title("Evidence completeness by CSF 2.0 function",
                 fontsize=12.5, fontweight="bold", color="#1F2A44")
    ax.grid(axis="y", ls=":", alpha=0.5)
    for b, p in zip(bars, pct):
        ax.text(b.get_x() + b.get_width() / 2, p + 2, f"{p:.0f}%", ha="center", fontsize=9, fontweight="bold")
    plt.tight_layout(); fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


# ---------- CSV outputs -----------------------------------------------------
def write_matrix_csv(results, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["CSF", "ISO_refs", "Control_evidence_expected", "Required",
                    "Status", "Score", "Newest_evidence", "Freshness_days", "Matched_files"])
        for r in results:
            w.writerow([r["csf"], "; ".join(r["iso"]), r["title"], r["required"],
                        r["status"], r["score"],
                        r["newest"].isoformat() if r["newest"] else "",
                        r["freshness_days"],
                        "; ".join(m["file"] for m in r["matched"])])


def write_ai_csv(ai_results, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Document", "AI_mode", "Summary", "Suggested_controls",
                    "Potential_gaps", "Validation_status", "Human_decision"])
        for a in ai_results:
            w.writerow([a["filename"], a["mode"], a["summary"],
                        "; ".join(f'{s["csf"]} ({s.get("why","")})' for s in a["suggested_controls"]),
                        " | ".join(a["potential_gaps"]),
                        a["validation_status"], ""])  # blank column for human sign-off


# ---------- report ----------------------------------------------------------
def write_report(results, ai_results, by_func, overall, files, ai_mode, today, path):
    present = sum(1 for r in results if r["status"] == "PRESENT")
    stale = sum(1 for r in results if r["status"] == "STALE")
    missing = sum(1 for r in results if r["status"] == "MISSING")
    with open(path, "w") as f:
        w = f.write
        w("# Evidence Analysis Report\n\n")
        w(f"Assessment date: **{today.isoformat()}**  |  Evidence files scanned: **{len(files)}**  "
          f"|  Controls checked: **{len(results)}**  |  AI mode: **{ai_mode}**\n\n")
        w("> **How to read this.** The completeness check (present/stale/missing) is deterministic "
          "and auditable. The AI section is **decision-support only** — every suggestion is labelled "
          "*pending human review*, and a control owner must confirm it before it becomes a finding.\n\n")

        w("## 1. Completeness summary (deterministic)\n\n")
        w(f"- Overall evidence completeness: **{overall*100:.0f}%**\n")
        w(f"- PRESENT: **{present}**  |  STALE: **{stale}**  |  MISSING: **{missing}**  (of {len(results)})\n\n")
        w("| CSF function | Complete % | Present | Stale | Missing |\n|---|---|---|---|---|\n")
        for fn in [x for x in ["GV", "ID", "PR", "DE", "RS", "RC"] if x in by_func]:
            d = by_func[fn]
            w(f"| {FUNCTIONS[fn]} | {d['score']/d['n']*100:.0f}% | {d['present']} | {d['stale']} | {d['missing']} |\n")
        w("\n![Evidence completeness by function](evidence_completeness.png)\n\n")

        w("## 2. Control-by-control evidence matrix\n\n")
        w("| CSF | ISO | Evidence expected | Status | Newest | Matched files |\n|---|---|---|---|---|---|\n")
        for r in sorted(results, key=lambda x: {"MISSING": 0, "STALE": 1, "PRESENT": 2}[x["status"]]):
            mf = ", ".join(m["file"] for m in r["matched"]) or "—"
            nd = r["newest"].isoformat() if r["newest"] else "—"
            w(f"| {r['csf']} | {', '.join(r['iso'])} | {r['title']} | **{r['status']}** | {nd} | {mf} |\n")
        w("\n")

        w("### Priority gaps (missing required evidence)\n\n")
        miss = [r for r in results if r["status"] == "MISSING" and r["required"]]
        if miss:
            for r in miss:
                w(f"- **{r['csf']}** ({', '.join(r['iso'])}) — {r['title']}: *no evidence found.*\n")
        else:
            w("- None — all required controls have at least some evidence.\n")
        stales = [r for r in results if r["status"] == "STALE"]
        if stales:
            w("\n**Stale evidence (exists but past its freshness window — re-collect):**\n\n")
            for r in stales:
                w(f"- **{r['csf']}** — {r['title']}: newest evidence {r['newest'].isoformat()} "
                  f"(limit {r['freshness_days']} days).\n")
        w("\n")

        w('<div class="pagebreak"></div>\n\n')
        w("## 3. AI-assisted document analysis — PENDING HUMAN REVIEW\n\n")
        w("Each document was analysed to draft a summary, suggest supported controls, and flag "
          "potential gaps. **These are AI suggestions, not findings.** A control owner signs off in "
          "the `evidence_ai_suggestions.csv` `Human_decision` column.\n\n")
        for a in ai_results:
            w(f"### {a['filename']}  \n")
            w(f"*AI mode: {a['mode']} · confidence: {a['confidence']} · status: {a['validation_status']}*\n\n")
            w(f"**Summary.** {a['summary']}\n\n")
            if a["suggested_controls"]:
                w("**Suggested controls (confirm each):** " +
                  ", ".join(f'{s["csf"]}' for s in a["suggested_controls"]) + "\n\n")
            if a["potential_gaps"]:
                w("**Potential gaps to check:**\n")
                for g in a["potential_gaps"]:
                    w(f"- {g}\n")
                w("\n")
        w("---\n\n")
        w("<div class=\"small\">AI suggestions generated for decision support only and must be validated "
          "by a qualified reviewer. In mock mode the analysis is an offline keyword heuristic, not a "
          "language model. This tool does not constitute an audit or certification.</div>\n")


# ---------- main ------------------------------------------------------------
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Evidence Analysis Pipeline (CSF 2.0 / ISO 27001)")
    ap.add_argument("--evidence", default=os.path.join(here, "..", "evidence"))
    ap.add_argument("--outdir", default=os.path.join(here, "..", "output"))
    ap.add_argument("--ai-mode", default="auto", choices=["auto", "mock", "real"])
    ap.add_argument("--today", default=None, help="override assessment date (YYYY-MM-DD)")
    args = ap.parse_args()

    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    if not os.path.isdir(args.evidence):
        sys.exit(f"ERROR: evidence folder not found: {args.evidence}")
    os.makedirs(args.outdir, exist_ok=True)

    files = scan_evidence(args.evidence, today)
    results = match(files, today)
    by_func, overall = summarise(results)
    mode = active_mode(args.ai_mode)
    ai_results = [analyze_document(fo["text"], fo["name"], EVIDENCE_RULES, mode=args.ai_mode)
                  for fo in files]

    matrix = os.path.join(args.outdir, "evidence_matrix.csv")
    aicsv = os.path.join(args.outdir, "evidence_ai_suggestions.csv")
    chart = os.path.join(args.outdir, "evidence_completeness.png")
    report = os.path.join(args.outdir, "evidence_report.md")
    write_matrix_csv(results, matrix)
    write_ai_csv(ai_results, aicsv)
    completeness_chart(by_func, chart)
    write_report(results, ai_results, by_func, overall, files, mode, today, report)

    present = sum(1 for r in results if r["status"] == "PRESENT")
    stale = sum(1 for r in results if r["status"] == "STALE")
    missing = sum(1 for r in results if r["status"] == "MISSING")
    print("=" * 60)
    print("EVIDENCE ANALYSIS PIPELINE")
    print("=" * 60)
    print(f"Evidence files scanned : {len(files)}")
    print(f"Controls checked       : {len(results)}")
    print(f"Overall completeness   : {overall*100:.0f}%")
    print(f"PRESENT {present}  |  STALE {stale}  |  MISSING {missing}")
    print(f"AI layer mode          : {mode}  ("
          f"{'live Anthropic API' if mode=='real' else 'offline heuristic — set ANTHROPIC_API_KEY for real mode'})")
    print("-" * 60)
    for r in results:
        tag = {"PRESENT": "[ok] ", "STALE": "[!!] ", "MISSING": "[XX] "}[r["status"]]
        print(f"  {tag}{r['csf']:<9} {r['status']:<8} {r['title'][:42]}")
    print("-" * 60)
    for p in (matrix, aicsv, chart, report):
        print("  -", os.path.abspath(p))


if __name__ == "__main__":
    main()
