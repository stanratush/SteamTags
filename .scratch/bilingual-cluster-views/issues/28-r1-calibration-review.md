# 28: R1 Calibration review

**What to build:** the researcher's first read of the Bulgarian, early enough that a systematic fault in tone, register or terms is fixed once, not in ten guide slices. The output is a list of corrections for issue 29 and a decision on every term marked "proposed".

**Blocked by:** 27

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Review (HITL)", "Corrections flow through the term table". Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

Checklist for the researcher. The agent prepares the session: it starts the app and lists the proposed terms and the slices' screenshots.

- [ ] **The app in BG**, all three modes:
  - **Workbench**: Controls, every tab, the Inspector for a tag, a Cluster (with Games and Connections), a pair and a link, both cards.
  - **Analysis Report mode.**
  - **Parameter Selection**: Run, the loading panel, the strip, "Why this pair", the Pair Inspector and the validation card.
- [ ] **G1 in Markdown**: `docs/user-guide/bg/` 00, 01, README, 06, Appendix A and Appendix C.
- [ ] Judge in particular:
  - the register (*вие*, imperative buttons);
  - the term choices in context;
  - the In short blocks' tone, against the banned quality words;
  - the number format;
  - anything that reads as translated rather than written.
- [ ] Decide each "proposed" row in `bg-terms.md`: accept it, or give the word.
- [ ] Mark corrections in any form: inline edits in the files, or a list in this issue's Comments with the screen or file and the line.
- [ ] Say whether the remaining guide slices (G2–G10) may start after issue 29 as they are, or need a different instruction. Any new instruction is added to the spec's Guide slice conventions by issue 29.

## Resolution

**2026-10-29, the researcher (recorded by the agent):** "Accept all proposed and continue with the next issue."

- **Term decisions:** every row marked "proposed" in `bg-terms.md` is accepted as written, from A1–A4 (issues 23–26) and G1 (issue 27). No term changes, so nothing goes to Superseded words.
- **Wording corrections:** none.
- **The "Choices for R1" listed in issues 24–27** stand as the slices made them, the shared "Multi-Tag Cluster" key included.
- **Guide slices G2–G10** start after issue 29 with the spec's Guide slice conventions unchanged.
