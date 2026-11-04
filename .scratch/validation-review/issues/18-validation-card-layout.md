# 18: The validation card's Cluster list and header

**What to build:** the card takes the interval-plot layout. An H4 header with a help link replaces the bold title, a warning note covers `no_qualifying_pair`, the Null Comparison and Subsample Stability get H5 headings, and the Cluster list (one row per Multi-Tag Cluster: size, a dot-and-whisker of the dissolution frequency per arm, status chips, an expandable row with every figure) replaces `cluster_table`. It fits at every app width in English and Bulgarian.

**Blocked by:** 17

**Status:** ready-for-agent

Spec: [Validation review spec](../spec.md): "The card", "Bulgarian". Reference layout and CSS, not to import: [PROTOTYPE-validation-layout.html](../prototypes/06-validation-layout/PROTOTYPE-validation-layout.html) (layout C). Verbatim strings: [bg-strings.md](../prototypes/11-bg-wording/bg-strings.md) ("Card" and "Cluster list" tables). Sources: [How should the validation card and the Inspector's Validation section look?](06-validation-card-and-inspector-layout.md) and its Comments, [What is the bg wording…?](11-bg-wording-card-and-inspector.md).

- [ ] **Header:** `html.H4` "Validation of g = …, s = …" with `_help("selection.validate")`.
- [ ] **Constraints note:** the existing muted sentence when custom constraints choose another pair; a warning note "No pair qualifies under your constraints, so this is the validation of g = …, s = …, the pair chosen under the default constraints." when `view.star` is None.
- [ ] **Sections:** H5 "Null Comparison" and H5 "Subsample Stability", each with its ? link, the muted headers, then issue 17's prose.
- [ ] **Cluster list** (new `ps_view.cluster_list`, replacing `cluster_table`):
  - the legend: "Share of subsamples with Hennig's Jaccard ≤ 0.5, with its 95% Wilson interval. R = re-selected, A = at resolution." + "Click a row for every figure.";
  - the header row Cluster | Size (44 px, ? help with the small-Cluster caveat) | "≤ 0.5: 0 — ½ — 1" | Status;
  - one `html.Details` row per Multi-Tag Cluster in Cluster order: label and up to 3 member tags; |C|; the R and A plot lines (dot at k/B*, whisker at the Wilson interval, dashed line at ½; dark when Dissolved in most subsamples in that arm, hollow grey otherwise; "Not assessable" in words when B* = 0), drawn with absolutely positioned CSS spans; the chips "Not assessable" (grey), "Dissolved in most subsamples" (dark), "borderline" (dashed), once when the arms agree, "R … A …" when they differ; "⚑ rarely assessable (B* of S)" under the status;
  - the expanded `Summary` content: Arm | Hennig's J (mean ± s.e.; 10th–90th pct) | ≤ 0.5 in (k of B*; 95% Wilson) | > 0.75 in (k of B*; 95% Wilson) | Whole-Cluster J (mean ± s.e.), then every member tag. Wilson intervals as "42–62%", compact ranges with an en dash;
  - under about 650 px of card width, the Status cell wraps onto its own line.
- [ ] **Closing lines** and the three help links, as today.
- [ ] **Catalogue:** every new `ps_view` key in `i18n/bg/ps_view.py`; the retired `ps_view` card keys removed.
- [ ] **Fit**, checked in the browser at wide 1280 and 1600, medium 1100 and narrow 800, in EN and BG, with a row expanded: no overflow, no overlap. Screenshots of wide 1280 and narrow 800 in both languages in Comments.
- [ ] App-render tests: the `no_qualifying_pair` note; a Cluster list row for each status combination (agreeing and differing arms, Not assessable, rarely assessable).
- [ ] The catalogue parity test and the full test suite pass.
