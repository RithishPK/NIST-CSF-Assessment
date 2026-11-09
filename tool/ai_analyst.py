"""
ai_analyst.py — the AI-assisted layer of the evidence pipeline (Priority 3).

For each evidence document it drafts:
  - a short summary,
  - which controls the document likely supports (suggested),
  - potential gaps or weaknesses an analyst should check.

HUMAN-IN-THE-LOOP BY DESIGN
---------------------------
Every result is returned with validation_status = "PENDING_HUMAN_REVIEW" and is
clearly labelled AI-SUGGESTED. The pipeline never treats an AI suggestion as a
finding — a human control owner confirms or rejects it. This mirrors how AI is
used responsibly in real GRC work: the model accelerates analysis; the human is
accountable for the conclusion.

TWO MODES
---------
- mock  (default): a transparent, offline heuristic. No API key, no network, fully
  repeatable — so the pipeline runs anywhere, including CI and this repo's demo.
- real  (optional): calls the Anthropic API when ANTHROPIC_API_KEY is set AND the
  `anthropic` package is installed. Falls back to mock on any error.

Select explicitly with analyze_document(..., mode="mock"|"real"|"auto").
"""
from __future__ import annotations
import os
import re
import json

MODEL = "claude-opus-4-8"           # used only in real mode
DISCLAIMER = "AI-SUGGESTED — PENDING HUMAN REVIEW. Not an audit finding."


# --------------------------------------------------------------------------
def _mode_available(mode: str) -> str:
    """Resolve 'auto' to 'real' only if a key and the SDK are both present."""
    if mode == "mock":
        return "mock"
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    try:
        import anthropic  # noqa: F401
        has_sdk = True
    except Exception:
        has_sdk = False
    if mode == "real":
        return "real" if (has_key and has_sdk) else "mock"
    # auto
    return "real" if (has_key and has_sdk) else "mock"


# --------------------------------------------------------------------------
def _mock_analyze(text: str, filename: str, rules) -> dict:
    """
    Deterministic, offline stand-in for an LLM. Transparent on purpose: it uses
    the same keyword signals a human would scan for, so its 'suggestions' are
    explainable and safe to demo. Clearly labelled as a heuristic.
    """
    low = text.lower()
    suggested = []
    for r in rules:
        hit = [k for k in r["keywords"] if k in low]
        if hit or any(h in filename.lower() for h in r["filename_hints"]):
            suggested.append({"csf": r["csf"], "iso": r["iso"],
                              "why": f"mentions {hit[0]!r}" if hit else "filename match"})

    # a short extractive summary: first non-heading sentence(s), whitespace collapsed
    clean = re.sub(r"\s+", " ", re.sub(r"[#*`>|]", " ", text)).strip()
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    summary = " ".join(s.strip() for s in sentences if len(s.strip()) > 25)[:300] or filename

    # heuristic potential gaps
    gaps = []
    if "backup" in low and "test" not in low and "restore" not in low:
        gaps.append("Backups mentioned but no evidence of restore testing.")
    if "partial" in low or "overdue" in low or "not in backup" in low:
        gaps.append("Document itself notes an incomplete or overdue control — verify remediation.")
    if "review" in low and not re.search(r"20\d\d", text):
        gaps.append("Review mentioned without a clear date — confirm it is current.")
    if "encrypt" not in low and ("guest data" in low or "personal data" in low):
        gaps.append("Handles personal data; confirm encryption at rest is in place.")
    if not suggested:
        gaps.append("Could not confidently link this document to a known control — route to a human.")

    return {
        "mode": "mock",
        "model": "offline-heuristic",
        "filename": filename,
        "summary": summary,
        "suggested_controls": suggested,
        "potential_gaps": gaps,
        "confidence": "low (heuristic)",
        "validation_status": "PENDING_HUMAN_REVIEW",
        "disclaimer": DISCLAIMER,
    }


# --------------------------------------------------------------------------
def _real_analyze(text: str, filename: str, rules) -> dict:
    """Call the Anthropic API. Falls back to mock on any error."""
    try:
        import anthropic
        client = anthropic.Anthropic()
        catalogue = "\n".join(f'- {r["csf"]} ({", ".join(r["iso"])}): {r["title"]}' for r in rules)
        prompt = (
            "You are a GRC analyst assistant. Analyse the evidence document below for a NIST CSF 2.0 / "
            "ISO 27001:2022 assessment. Return STRICT JSON with keys: summary (<=50 words), "
            "suggested_controls (list of {csf, why}), potential_gaps (list of strings). "
            "Only suggest controls from this catalogue:\n" + catalogue +
            f"\n\n--- DOCUMENT: {filename} ---\n" + text[:6000]
        )
        msg = client.messages.create(
            model=MODEL, max_tokens=900,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text
        data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
        data.update({"mode": "real", "model": MODEL, "filename": filename,
                     "confidence": "model-generated",
                     "validation_status": "PENDING_HUMAN_REVIEW", "disclaimer": DISCLAIMER})
        # normalise iso onto suggestions from the catalogue
        idx = {r["csf"]: r["iso"] for r in rules}
        for s in data.get("suggested_controls", []):
            s.setdefault("iso", idx.get(s.get("csf"), []))
        return data
    except Exception as e:
        fb = _mock_analyze(text, filename, rules)
        fb["note"] = f"real mode failed ({type(e).__name__}); fell back to mock"
        return fb


# --------------------------------------------------------------------------
def analyze_document(text: str, filename: str, rules, mode: str = "auto") -> dict:
    """Public entry point. mode: 'auto' (default), 'mock', or 'real'."""
    resolved = _mode_available(mode)
    if resolved == "real":
        return _real_analyze(text, filename, rules)
    return _mock_analyze(text, filename, rules)


def active_mode(mode: str = "auto") -> str:
    return _mode_available(mode)


if __name__ == "__main__":
    from evidence_rules import EVIDENCE_RULES
    sample = ("# Backup and Restore Test Log\nLast restore test date: 2026-02-10\n"
              "Result: PARTIAL — database restored, but guest ID scan folder was not in backup set.")
    import pprint
    print("Active mode:", active_mode())
    pprint.pprint(analyze_document(sample, "backup_test_log.md", EVIDENCE_RULES, mode="mock"))
