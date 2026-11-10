#!/usr/bin/env python3
"""
score.py - NIST CSF 2.0 maturity scoring engine.

Reads a completed assessment workbook (the Assessment sheet) and produces:
  - a category x function maturity HEATMAP (PNG)
  - a current-vs-target bar chart by function (PNG)
  - a prioritised remediation ROADMAP (Markdown + CSV)
  - a printed summary to the console

Usage:
    python score.py --input ../assessment/CSF2.0_Maturity_Assessment.xlsx \
                    --outdir ../output

If --input is omitted it defaults to the bundled workbook.

Only standard data-science libs: openpyxl, pandas, matplotlib, numpy.
"""
from __future__ import annotations
import argparse
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from openpyxl import load_workbook

from csf_data import FUNCTIONS, CATEGORIES

FUNC_ORDER = ["GV", "ID", "PR", "DE", "RS", "RC"]
# red -> amber -> green, matching the workbook heatmap
CMAP = LinearSegmentedColormap.from_list(
    "csf", ["#f8696b", "#ffeb84", "#63be7b"])


# --------------------------------------------------------------------------
def read_assessment(path: str) -> pd.DataFrame:
    """Load the Assessment sheet into a tidy DataFrame."""
    wb = load_workbook(path, data_only=True)
    if "Assessment" not in wb.sheetnames:
        sys.exit(f"ERROR: no 'Assessment' sheet in {path}")
    ws = wb["Assessment"]

    # locate header row (the one containing 'ID')
    header_row = None
    for r in range(1, 15):
        if ws.cell(row=r, column=2).value == "ID":
            header_row = r
            break
    if header_row is None:
        sys.exit("ERROR: could not find the header row (expected 'ID' in column B).")

    rows = []
    for r in range(header_row + 1, ws.max_row + 1):
        sid = ws.cell(row=r, column=2).value
        if not sid or "." not in str(sid):
            continue
        cur = ws.cell(row=r, column=5).value
        tgt = ws.cell(row=r, column=6).value
        cur = 0 if cur is None else int(cur)
        tgt = 0 if tgt is None else int(tgt)
        func = str(sid).split(".")[0]
        catid = str(sid).rsplit("-", 1)[0]
        rows.append({
            "id": sid,
            "function": func,
            "function_name": FUNCTIONS.get(func, func),
            "category": catid,
            "category_name": CATEGORIES.get(catid, catid),
            "outcome": ws.cell(row=r, column=4).value,
            "current": cur,
            "target": tgt,
            "gap": max(0, tgt - cur),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        sys.exit("ERROR: no scored subcategories found.")
    # priority weight: gap, boosted when the current score is low
    df["weight"] = df["gap"] + (4 - df["current"]) / 2
    df["priority"] = pd.cut(
        np.where(df["gap"] == 0, -1, df["weight"]),
        bins=[-2, 0, 2, 3.5, 99],
        labels=["None", "Low", "Medium", "High"],
    )
    return df


# --------------------------------------------------------------------------
def summarise(df: pd.DataFrame) -> pd.DataFrame:
    g = (df.groupby("function", sort=False)
           .agg(current=("current", "mean"),
                target=("target", "mean"),
                gap=("gap", "mean"),
                n=("id", "count"))
           .reindex(FUNC_ORDER))
    g["pct_to_target"] = np.where(g["target"] == 0, 1.0, g["current"] / g["target"])
    g["function_name"] = [FUNCTIONS[f] for f in g.index]
    return g.round(2)


# --------------------------------------------------------------------------
def heatmap(df: pd.DataFrame, outdir: str) -> str:
    """Category (rows) laid out under their function - current maturity heatmap."""
    cat_mean = (df.groupby(["function", "category", "category_name"], sort=False)["current"]
                  .mean().reset_index())
    cat_mean["function"] = pd.Categorical(cat_mean["function"], FUNC_ORDER, ordered=True)
    cat_mean = cat_mean.sort_values(["function", "category"])

    labels = [f'{r.category}  {r.category_name[:34]}' for r in cat_mean.itertuples()]
    vals = cat_mean["current"].to_numpy().reshape(-1, 1)

    fig, ax = plt.subplots(figsize=(8.5, 11))
    im = ax.imshow(vals, cmap=CMAP, vmin=0, vmax=4, aspect="auto")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xticks([0]); ax.set_xticklabels(["Current maturity"], fontsize=10)
    for i, v in enumerate(vals.flatten()):
        ax.text(0, i, f"{v:.1f}", ha="center", va="center",
                fontsize=9, fontweight="bold",
                color="#222" if 0.8 < v < 3.2 else "#111")
    # function separators
    prev = None
    for i, f in enumerate(cat_mean["function"]):
        if prev is not None and f != prev:
            ax.axhline(i - 0.5, color="#1F2A44", lw=2)
        prev = f
    ax.set_title("NIST CSF 2.0 - Maturity Heatmap by Category",
                 fontsize=13, fontweight="bold", color="#1F2A44", pad=14)
    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.04)
    cbar.set_label("Maturity (0 = none  ->  4 = adaptive)", fontsize=9)
    plt.tight_layout()
    path = os.path.join(outdir, "heatmap.png")
    fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)
    return path


def bar_chart(summary: pd.DataFrame, outdir: str) -> str:
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(summary)); w = 0.38
    ax.bar(x - w/2, summary["current"], w, label="Current", color="#C0392B")
    ax.bar(x + w/2, summary["target"], w, label="Target", color="#2E5A88")
    ax.set_xticks(x); ax.set_xticklabels(summary["function_name"], fontsize=9)
    ax.set_ylim(0, 4); ax.set_ylabel("Maturity (0-4)")
    ax.set_title("Current vs Target Maturity by Function",
                 fontsize=13, fontweight="bold", color="#1F2A44")
    ax.legend(); ax.grid(axis="y", ls=":", alpha=0.5)
    for i, (c, t) in enumerate(zip(summary["current"], summary["target"])):
        ax.text(i - w/2, c + 0.05, f"{c:.1f}", ha="center", fontsize=8)
        ax.text(i + w/2, t + 0.05, f"{t:.1f}", ha="center", fontsize=8)
    plt.tight_layout()
    path = os.path.join(outdir, "maturity_by_function.png")
    fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)
    return path


# --------------------------------------------------------------------------
def roadmap(df: pd.DataFrame, summary: pd.DataFrame, outdir: str, top_n: int = 25):
    road = (df[df["gap"] > 0]
            .sort_values(["weight", "gap"], ascending=False)
            .head(top_n).reset_index(drop=True))
    road.index += 1

    csv_cols = ["id", "function_name", "category_name", "outcome",
                "current", "target", "gap", "priority"]
    csv_path = os.path.join(outdir, "roadmap.csv")
    road[csv_cols].to_csv(csv_path, index_label="rank")

    md = os.path.join(outdir, "roadmap.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write("# NIST CSF 2.0 - Prioritised Remediation Roadmap\n\n")
        f.write(f"Overall current maturity: **{df['current'].mean():.2f} / 4**  ")
        f.write(f"| target: **{df['target'].mean():.2f} / 4**  ")
        f.write(f"| {(df['current'].mean()/df['target'].mean()*100):.0f}% of target reached\n\n")

        f.write("## Maturity by function\n\n")
        f.write("| Function | Current | Target | Gap | % to target |\n")
        f.write("|---|---|---|---|---|\n")
        for fcode, row in summary.iterrows():
            f.write(f"| {row['function_name']} ({fcode}) | {row['current']:.2f} | "
                    f"{row['target']:.2f} | {row['gap']:.2f} | {row['pct_to_target']*100:.0f}% |\n")

        f.write(f"\n## Top {len(road)} actions (worst gap first)\n\n")
        f.write("| # | ID | Outcome | Cur | Tgt | Gap | Priority |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for i, r in road.iterrows():
            f.write(f"| {i} | {r['id']} | {r['outcome']} | {r['current']} | "
                    f"{r['target']} | {r['gap']} | {r['priority']} |\n")
        f.write("\n*Priority weights the gap by how low the current score is, "
                "so foundational gaps surface first.*\n")
    return csv_path, md, road


# --------------------------------------------------------------------------
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default_in = os.path.join(here, "..", "assessment", "CSF2.0_Maturity_Assessment.xlsx")
    default_out = os.path.join(here, "..", "output")

    ap = argparse.ArgumentParser(description="Score a NIST CSF 2.0 maturity assessment.")
    ap.add_argument("--input", default=default_in, help="path to the assessment .xlsx")
    ap.add_argument("--outdir", default=default_out, help="where to write charts + roadmap")
    ap.add_argument("--top", type=int, default=25, help="number of roadmap items")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    df = read_assessment(args.input)
    summary = summarise(df)

    hp = heatmap(df, args.outdir)
    bp = bar_chart(summary, args.outdir)
    csv_path, md_path, road = roadmap(df, summary, args.outdir, args.top)

    # console summary
    print("=" * 60)
    print("NIST CSF 2.0 MATURITY - SUMMARY")
    print("=" * 60)
    print(f"Subcategories scored : {len(df)}")
    print(f"Overall current      : {df['current'].mean():.2f} / 4")
    print(f"Overall target       : {df['target'].mean():.2f} / 4")
    print(f"% of target reached  : {df['current'].mean()/df['target'].mean()*100:.0f}%")
    print("-" * 60)
    print(f"{'Function':<22}{'Cur':>6}{'Tgt':>6}{'Gap':>6}{'%Tgt':>7}")
    for fcode, row in summary.iterrows():
        print(f"{row['function_name']+' ('+fcode+')':<22}"
              f"{row['current']:>6.2f}{row['target']:>6.2f}{row['gap']:>6.2f}"
              f"{row['pct_to_target']*100:>6.0f}%")
    print("-" * 60)
    pc = df["priority"].value_counts()
    print(f"Priorities -> High: {pc.get('High',0)}  "
          f"Medium: {pc.get('Medium',0)}  Low: {pc.get('Low',0)}")
    print("-" * 60)
    print("Top 5 actions:")
    for i, r in road.head(5).iterrows():
        print(f"  {i:>2}. {r['id']:<9} gap {r['gap']}  [{r['priority']}]  {r['outcome'][:48]}")
    print("=" * 60)
    print("Written:")
    for p in (hp, bp, csv_path, md_path):
        print("  -", os.path.abspath(p))


if __name__ == "__main__":
    main()
