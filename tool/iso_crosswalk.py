#!/usr/bin/env python3
"""
iso_crosswalk.py - NIST CSF 2.0  <->  ISO/IEC 27001:2022 framework crosswalk.

Generates, from the curated mapping in iso27001_data.py:
  - crosswalk_csf_to_iso.csv   : every CSF subcategory and its ISO 27001:2022 refs
  - crosswalk_iso_to_csf.csv   : every referenced ISO control and the CSF subcats that hit it
  - crosswalk_report.md        : a readable framework-mapping report + coverage analysis
  - iso_coverage.png           : ISO Annex A coverage by theme (covered vs not covered by CSF)

Why this matters (the GRC use case): an organisation that assessed itself with CSF 2.0 can use
this crosswalk to see how far that work carries toward ISO/IEC 27001:2022 - which Annex A controls
are already touched, and which ISO controls a CSF assessment does NOT directly surface (the
"blind spots" to pick up separately for certification).

Usage:
    python iso_crosswalk.py [--outdir ../output]
"""
from __future__ import annotations
import argparse, csv, os, sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from csf_data import SUBCATEGORIES, CATEGORIES, FUNCTIONS
from iso27001_data import (ISO_CONTROLS, MANAGEMENT_CLAUSES, ISO_THEMES,
                           mapping_for, iso_ref_title, theme_of)


def build_rows():
    """One row per CSF subcategory with its ISO refs."""
    rows = []
    for sid, outcome, cur, tgt, note in SUBCATEGORIES:
        refs = mapping_for(sid)
        rows.append({
            "csf_id": sid,
            "function": FUNCTIONS[sid.split(".")[0]],
            "category": CATEGORIES[sid.rsplit("-", 1)[0]],
            "outcome": outcome,
            "iso_refs": refs,
            "iso_titles": [iso_ref_title(r) for r in refs],
        })
    return rows


def write_forward_csv(rows, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["CSF_Subcategory", "Function", "Category", "CSF_Outcome",
                    "ISO27001_2022_Refs", "ISO27001_2022_Titles"])
        for r in rows:
            w.writerow([r["csf_id"], r["function"], r["category"], r["outcome"],
                        "; ".join(r["iso_refs"]),
                        " | ".join(f"{ref} {t}" for ref, t in zip(r["iso_refs"], r["iso_titles"]))])


def build_reverse(rows):
    """ISO ref -> list of CSF subcats that map to it."""
    rev = defaultdict(list)
    for r in rows:
        for ref in r["iso_refs"]:
            rev[ref].append(r["csf_id"])
    return rev


def write_reverse_csv(rev, path):
    def sortkey(ref):
        # clauses first, then A.x.y numerically
        if ref.startswith("Cl."):
            return (0, int(ref.split(".")[1]), 0)
        _, a, b = ref.split(".")
        return (1, int(a), int(b))
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ISO27001_2022_Ref", "Type", "ISO_Title", "Num_CSF_Subcats", "CSF_Subcategories"])
        for ref in sorted(rev, key=sortkey):
            w.writerow([ref, theme_of(ref), iso_ref_title(ref),
                        len(rev[ref]), "; ".join(rev[ref])])


def coverage_stats(rev):
    """Which of the 93 Annex A controls are / are not referenced by any CSF subcategory."""
    covered = {r for r in rev if r in ISO_CONTROLS}
    uncovered = [c for c in ISO_CONTROLS if c not in covered]
    by_theme_total = defaultdict(int)
    by_theme_cov = defaultdict(int)
    for c in ISO_CONTROLS:
        th = theme_of(c)
        by_theme_total[th] += 1
        if c in covered:
            by_theme_cov[th] += 1
    return covered, uncovered, by_theme_total, by_theme_cov


def coverage_chart(by_theme_total, by_theme_cov, path):
    themes = ["Organizational", "People", "Physical", "Technological"]
    cov = [by_theme_cov.get(t, 0) for t in themes]
    tot = [by_theme_total.get(t, 0) for t in themes]
    notcov = [tt - cc for tt, cc in zip(tot, cov)]
    import numpy as np
    x = np.arange(len(themes))
    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax.bar(x, cov, 0.6, label="Touched by a CSF 2.0 subcategory", color="#2E5A88")
    ax.bar(x, notcov, 0.6, bottom=cov, label="Not directly touched (ISO-only)", color="#C0392B")
    ax.set_xticks(x); ax.set_xticklabels([f"{t}\n(A.{i+5})" for i, t in enumerate(themes)], fontsize=9)
    ax.set_ylabel("ISO/IEC 27001:2022 Annex A controls")
    ax.set_title("ISO 27001:2022 Annex A coverage by a NIST CSF 2.0 assessment",
                 fontsize=12.5, fontweight="bold", color="#1F2A44")
    ax.legend(fontsize=8.5)
    for i, (c, t) in enumerate(zip(cov, tot)):
        ax.text(i, t + 0.4, f"{c}/{t}", ha="center", fontsize=9, fontweight="bold")
    plt.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


def write_report(rows, rev, covered, uncovered, by_theme_total, by_theme_cov, path):
    total_links = sum(len(r["iso_refs"]) for r in rows)
    n_annex_cov = len(covered)
    with open(path, "w") as f:
        w = f.write
        w("# NIST CSF 2.0 ↔ ISO/IEC 27001:2022 Framework Crosswalk\n\n")
        w("A mapping between the 106 NIST CSF 2.0 subcategories and the ISO/IEC 27001:2022 "
          "Annex A controls (93) plus ISMS management clauses (4–10).\n\n")
        w("> **Sourcing & honesty.** The Annex A control titles are authoritative "
          "(ISO/IEC 27001:2022). The CSF→ISO *mapping* is a **curated, analyst-built crosswalk**, "
          "not a verbatim copy of NIST’s official Informative References. Framework mappings are "
          "many-to-many and involve judgement; validate against NIST’s official CSF 2.0 "
          "Informative References and ISO/IEC 27002:2022 before any certification use.\n\n")

        w("## Coverage summary\n\n")
        w(f"- CSF subcategories mapped: **{len(rows)} / 106**\n")
        w(f"- Total CSF→ISO mapping links: **{total_links}**\n")
        w(f"- ISO Annex A controls touched by a CSF assessment: **{n_annex_cov} / 93** "
          f"({n_annex_cov/93*100:.0f}%)\n")
        w(f"- ISO Annex A controls **not** directly surfaced by CSF: **{len(uncovered)}**\n\n")
        w("| ISO theme | Covered | Total | % |\n|---|---|---|---|\n")
        for t in ["Organizational", "People", "Physical", "Technological"]:
            c, tt = by_theme_cov.get(t, 0), by_theme_total.get(t, 0)
            w(f"| {t} | {c} | {tt} | {c/tt*100:.0f}% |\n")
        w("\n![ISO coverage by theme](iso_coverage.png)\n\n")

        w("## Interpretation (the GRC insight)\n\n")
        w("A completed NIST CSF 2.0 assessment gives an organisation a **running start toward "
          "ISO/IEC 27001:2022**: the mapped Annex A controls are already understood. The controls "
          "listed as *not directly surfaced* below are ISO’s **blind spots relative to CSF** — "
          "typically HR/people controls, physical specifics, and documentation items — which an "
          "organisation pursuing certification must pick up separately (chiefly via the ISO "
          "management clauses 4–10 and the Statement of Applicability).\n\n")

        w("### ISO Annex A controls NOT directly surfaced by a CSF 2.0 assessment\n\n")
        w("| ISO ref | Theme | Control |\n|---|---|---|\n")
        for c in uncovered:
            w(f"| {c} | {theme_of(c)} | {ISO_CONTROLS[c]} |\n")
        w("\n")

        w('<div class="pagebreak"></div>\n\n')
        w("## Forward crosswalk — CSF 2.0 → ISO/IEC 27001:2022\n\n")
        cur_func = None
        for r in rows:
            fn = r["function"]
            if fn != cur_func:
                w(f"\n### {fn}\n\n")
                w("| CSF ID | CSF outcome | ISO/IEC 27001:2022 refs |\n|---|---|---|\n")
                cur_func = fn
            refs = ", ".join(r["iso_refs"]) if r["iso_refs"] else "—"
            w(f"| {r['csf_id']} | {r['outcome']} | {refs} |\n")
        w("\n")

    return n_annex_cov, total_links


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="NIST CSF 2.0 <-> ISO 27001:2022 crosswalk generator")
    ap.add_argument("--outdir", default=os.path.join(here, "..", "output"))
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    rows = build_rows()
    rev = build_reverse(rows)
    covered, uncovered, tt, tc = coverage_stats(rev)

    fwd_csv = os.path.join(args.outdir, "crosswalk_csf_to_iso.csv")
    rev_csv = os.path.join(args.outdir, "crosswalk_iso_to_csf.csv")
    chart = os.path.join(args.outdir, "iso_coverage.png")
    report = os.path.join(args.outdir, "crosswalk_report.md")

    write_forward_csv(rows, fwd_csv)
    write_reverse_csv(rev, rev_csv)
    coverage_chart(tt, tc, chart)
    n_cov, links = write_report(rows, rev, covered, uncovered, tt, tc, report)

    print("=" * 60)
    print("NIST CSF 2.0  <->  ISO/IEC 27001:2022 CROSSWALK")
    print("=" * 60)
    print(f"CSF subcategories mapped : {len(rows)} / 106")
    print(f"Total mapping links      : {links}")
    print(f"ISO Annex A covered      : {n_cov} / 93 ({n_cov/93*100:.0f}%)")
    print(f"ISO Annex A not surfaced : {len(uncovered)}")
    print("-" * 60)
    for t in ["Organizational", "People", "Physical", "Technological"]:
        print(f"  {t:<16}: {tc.get(t,0):>2}/{tt.get(t,0):<2} covered")
    print("-" * 60)
    for p in (fwd_csv, rev_csv, chart, report):
        print("  -", os.path.abspath(p))


if __name__ == "__main__":
    main()
