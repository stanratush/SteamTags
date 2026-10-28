# Bulk translation slicing and review
Type: grilling
Status: resolved
Blocked by: none

## Question

How does the Bulgarian text get written and reviewed in implementation-sized slices? Uses `grilling` + `domain-modeling`. Works from the [String inventory](01-string-inventory.md), the [Translation mechanism](02-translation-mechanism.md) and the term table from [Bulgarian terminology](03-bulgarian-terminology.md) ([docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md)).

- **Slices**: how the ~500 app strings (by module: `view.py`, `ps_view.py`, `layout.py`, `selection_text.py`, …) and the ~43,600 hand-translated guide words (by guide file) split into issues of one agent session each, and where the new text of features 2–4 goes (the last slice, or each feature's own issues).
- **Strictness**: when the completeness checks (catalogue entries, guide headings) turn strict. At the last slice, or per module or file as each one is done.
- **Visibility**: whether the EN | BG switch stays hidden or marked as a preview until completeness passes, given that missing entries fall back to English at runtime.
- **Review**: how the researcher reviews (per slice or once at the end, in the app or in the Markdown files), and how corrections flow back into the table and the text.

## Answer

Settled with the researcher on 2026-10-28 in one grilling round (all seven recommendations accepted). No glossary term and no ADR: slicing and review are delivery plan, not domain or a hard-to-reverse choice.

- **Text from features 2–4 is English-only in each feature's own issues.** They write `tx("…")` and the English guide. Every bulk slice is blocked by the translation mechanism and by every feature issue, so the Bulgarian is written once, over finished English.
- **App slices (AFK), run first** (~100–150 sites each):
  - **A1**: `layout.py`, `callbacks.py`, the `OpenRefused` reasons, the `ui-words` store (JS/CSS words), grid `localeText`, and the schema header tooltips.
  - **A2**: `view.py`.
  - **A3**: `ps_view.py` and the `ps_run` ETA/elapsed text.
  - **A4**: `selection_text.py`, the In short label sets and the entry markers.
- **Guide slices (AFK)**, cut at `##` headings, each ≤ ~5,000 words. Word counts are from 2026-10-28:
  - **G1**: 00, 01, README, 06, Appendix A, Appendix C (~4.3k).
  - **G2**: 02 Control reference + Analytical controls explained (~3.9k, plus the feature 2–3 additions).
  - **G3**: 02 Reading the graph … Parameter Selection mode (~4.6k).
  - **G4**: 03 How to read this chapter + Settings that change the numbers + Ranking and data (~4.7k).
  - **G5**: 03 Feature analysis (~4.5k).
  - **G6**: 03 The Tag Network (~4.9k).
  - **G7**: 03 Clusters and partition quality (~3.9k, plus the feature 3–4 additions).
  - **G8**: 03 Stability + Removal Sensitivity (~4.5k).
  - **G9**: 03 Parameter Selection (~4.4k).
  - **G10**: 04 + 05 (~3.8k), plus generating the Bulgarian Appendix B with `export/column_index.py`.

  Slices that share a file (G2–G3 on 02, G4–G9 on 03) run one after another, never in parallel.
- **Strictness is a ratchet.** The completeness tests (catalogue entries, guide headings and labels) keep a "done" list of catalogue modules and guide files or `##` sections. Each slice adds its own entries, and from then on a missing or orphaned entry inside them fails. Correctness and structure checks stay strict from the start, as ADR 0003 says. The methods-paragraph verbatim test runs in Bulgarian once A4 and G10 are both done. **G10 deletes the list**, so completeness is then checked everywhere.
- **The EN | BG switch is visible and plain from when the mechanism lands.** No preview badge and no flag; missing text falls back to English. Nothing is released from `bilingual-cluster-views` until completeness is fully strict. G10 adds that check as a gate to the release checklist.
- **Review: two HITL issues.**
  - **R1, calibration**, after A1–A4 and G1. The researcher reads the app in BG in all three modes, and G1 in Markdown, for tone, register and terms. A follow-up AFK issue applies the corrections, and G2–G10 are blocked by it.
  - **R2, final**, after G10. The whole of `docs/user-guide/bg/` in Markdown, plus a last pass through the app in BG. A follow-up AFK issue applies the corrections.
- **Corrections flow back through the term table.** A term change edits `docs/i18n/bg-terms.md` first and moves the old word into that term's **Avoid** column. A new test scans `i18n/bg/*.py` and `docs/user-guide/bg/` for every Avoid word and fails on a hit, which forces the sweep. An exception list in `bg-terms.md` allows legitimate phrases (e.g. *откриване на общности*). The first slice to add Bulgarian text adds the test. Other wording corrections are marked by the researcher however they like (inline edits or a notes list) and applied in that review's follow-up issue.
