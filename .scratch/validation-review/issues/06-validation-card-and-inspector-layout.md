# How should the validation card and the Inspector's Validation section look?
Type: prototype
Status: resolved
Blocked by: 02, 04

## Question

The card and the Inspector need rework once the figures are fixed. See [Verified review](../research/01-verified-review.md) items 1 and 18–22.

The rework covers:
- one row per Cluster with grouped columns per arm (or an arm selector), a size column and a "Status" header;
- labelled ranges ("10th–90th percentile"; "range over D networks");
- shared vs arm-specific dissolved lists;
- the title as a heading with a help link;
- "Dissolved (re-selected): n" in the Inspector;
- the Validate button inside the Inspector's Validation section;
- a note saying which pair is shown when custom constraints give no qualifying pair;
- the heatmap held at 460 px (`flex-shrink: 0`) in the `.ps-main` column;
- the Null Comparison's new content, from [What does the Null Comparison state, and by which rule?](04-null-comparison-rule-and-wording.md): the Multi-Tag Cluster line, the D < R/2 weak-comparison flag, the three badge states (with "⚠"), and the header "per-pair procedure at g = …, s = …".

Prototype the wide and narrow forms in EN and BG and pick one.

## Answer

Decided 2026-11-04 by the researcher, from a prototype: [PROTOTYPE-validation-layout.html](../prototypes/06-validation-layout/PROTOTYPE-validation-layout.html), built on the real rpg 7/5 run with [dump_validation.py](../prototypes/06-validation-layout/dump_validation.py). Three layouts were compared at the app's widths (wide 1280 and 1600, medium 1100, narrow 800) in EN and a draft BG:
- **A, grouped table** (both arms side by side): rejected. At 865–957 px it overflows the 593 px card at wide 1280 and only fits in English at wide 1600.
- **B, arm selector** (one arm at a time, with the Null Comparison as a table): rejected.
- **C, interval plot**: **chosen**. It fits at every width in both languages and gives the shortest card.

**The card, top to bottom** (the main column, under "Why this pair")
1. **Header:** an H4 "Validation of g = 7, s = 5" with `_help("selection.validate")`, replacing the bold `P` (review item 22).
2. **Constraints note:**
   - Custom constraints choose another pair: the existing muted sentence "Validation ran for g = …, s = …, the pair chosen under the default constraints."
   - Custom constraints give `no_qualifying_pair` (`chosen_pair` None, review item 22): a warning note, "No pair qualifies under your constraints, so this is the validation of g = 7, s = 5, the pair chosen under the default constraints."
3. **Null Comparison:** an H5 with its ? link, followed by ticket 04's header in muted text: "(100 shuffled networks, per-pair procedure at g = 7, s = 5)". The section stays **prose**, in ticket 04's wording:
   - the Q sentence in its three states. When U > 0 the reasons follow it ("; 52 had no edges; 8 lay beyond their γ scan");
   - D < R/2: a warning note, "⚠ Most shuffled networks have no Q (60 of 100), so this comparison is weak.";
   - the Multi-Tag Cluster line, or "None of the 100 shuffled networks has a Selected Partition.";
   - the width sentence, then ticket 05's "Widths are upper bounds, conditional on the partitions the γ scan finds.";
   - `NULL_CAVEAT` in italics.
4. **Subsample Stability:** an H5 with its ? link and the muted header "(100 random 80% subsets of the games, g′ = 5, s′ = 4)." Then:
   - **ARI, with labelled spreads** (review item 18): "Re-selected: median ARI 0.54 (10th–90th percentile: 0.45 to 0.65) over 100 of 100 subsamples, on 99% of the tags." The degenerate reasons follow as today. Then "At resolution 2.006: median ARI 0.54 (10th–90th percentile: 0.45 to 0.65)." "on 99% of the tags" is ticket 01's `edged_share`.
   - **One combined dissolved list** (review item 20; ticket 02 left this to the layout): "**Dissolved in most subsamples** (Hennig's Jaccard ≤ 0.5 in more than half; the majority is this study's rule): 7 of 15 Multi-Tag Clusters in both arms: *C8*, …; re-selected only: *C7*; at resolution only: …". Empty groups are left out. This replaces ticket 02's one sentence per arm.
   - **Borderline**, in the same shape: "Borderline (the 95% Wilson interval contains ½): *C3*, *C4*, *C7*, *C10* in both arms." It appears only when there is at least one.
   - **Not assessable**, as its own sentence: "Not assessable (fewer than 2 of its tags survive in every subsample): *C15*."
   - "No Multi-Tag Cluster is dissolved in most subsamples in either arm." appears only when no Cluster is labelled and none is not assessable (ticket 02).
5. **The Cluster list**, which replaces `cluster_table` and its 2 × N rows (review item 21):
   - **Legend** (small, muted): "Share of subsamples with Hennig's Jaccard ≤ 0.5, with its 95% Wilson interval. R = re-selected, A = at resolution. Click a row for every figure."
   - **Header row:** Cluster | Size (with the ticket 01 small-Cluster caveat as its ? help) | "≤ 0.5: 0 — ½ — 1" | **Status**.
   - **One row per Multi-Tag Cluster**, in Cluster order:
     - the label, with up to 3 member tags beneath it;
     - the size |C|;
     - a dot-and-whisker plot, about 150 px wide, with two lines: R and A. Each line shows the dissolution frequency k/B* as a dot, with its Wilson interval as the whisker, on a 0–1 axis with a dashed line at ½. The dot and whisker are filled dark when the Cluster is Dissolved in most subsamples in that arm, and hollow and grey otherwise. A whisker crossing ½ is borderline. A not-assessable arm shows the words "Not assessable" instead of a whisker;
     - the status chips: "Not assessable" (grey), "Dissolved in most subsamples" (dark) and "borderline" (dashed outline). When the arms agree, the chips appear once. When they differ, they read "R … A …".
     - "⚑ rarely assessable (B* of S)" under the status, when it applies.
   - **Narrow cards:** below about 650 px (wide form at 1280), the Status cell wraps onto its own line under the row.
   - **Expanding a row** shows every figure for both arms in a small table: Arm | Hennig's J (mean ± s.e.; 10th–90th percentile) | ≤ 0.5 in (k of B*; 95% Wilson) | > 0.75 in (k of B*; 95% Wilson) | Whole-Cluster J (mean ± s.e.). All member tags are listed under it. Wilson intervals read "42–62%".
6. **Closing lines:** `SUBSAMPLE_CAVEAT` and ticket 04's limitation sentence, both in italics, then the existing "Three kinds of stability · Null Comparison · Subsample Stability" links.

**Implementation notes (from the prototype, not binding on the code):**
- **Row expansion:** use `html.Details`/`Summary` per row. It needs no callback and is keyboard-accessible.
- **The whiskers:** draw them with absolutely positioned CSS spans, not Plotly. Dash has no inline-SVG component in core.

**The Inspector's Validation section** (at the bottom of the Inspector body)
- **Header:** an H5 "Validation" with its ? link.
- **Not validated:** "Not validated", and under it the **Validate this pair** button, moved here from under Apply (review item 22). The prototype also showed a run-time hint, which is dropped: nobody asked for it.
- **Validated:**
  - **Badges:** ticket 04's null badge, in its three states with the "⚠" suffix and the help link on "Q not above the null", followed by "Dissolved in most subsamples (re-selected): n". That badge answers review item 22's "Dissolved: n".
  - **Status strips:** two strips, R and A, with one 12 px square per Multi-Tag Cluster in Cluster order. Dark means dissolved in most subsamples, a dashed outline means borderline, and hatching means not assessable. Each square's tooltip is the Cluster's label.
  - The small line "median ARI re-selected 0.54, at resolution 0.54".
  - **A link "Open the validation card ↓"**, which scrolls the main column to the card. It appears **only when the inspected pair is the card's pair**: the card always shows the default-constraint pair, while the Inspector shows the inspected pair's own validation.

**Heatmap** (review item 1): `#ps-heatmap{flex:0 0 460px}`, plus `flex-shrink:0` on every direct child of `.ps-main`, which scrolls. In the prototype the card no longer squeezes the heatmap.

**Not on the card:**
- **Ticket 03's residual sentence** ("50 seeds raised a null's Q by at most 0.0013") goes in the guide only.
- **Perturbation Share**, edge ratio and null resolution stay in the export and the guide only (tickets 04 and 05).

**BG:** the prototype's Bulgarian is a draft, written to test fit. Every string fitted at every width. The final wording is graduated to [What is the bg wording of the validation card and the Inspector's Validation section?](11-bg-wording-card-and-inspector.md).

**Prototype capture:** the prototype and its dump script stay in `prototypes/06-validation-layout/`, uncommitted. Two parts of it are stand-ins:
- **Whole-Cluster Jaccard** is approximated as Hennig's J × retention, because |D′| is not stored.
- **The reached, undefined and weak null states** are synthesised.

**Hand-offs**
- To [How are versions, reruns and tests staged?](07-versioning-reruns-and-tests.md): golden texts for the combined dissolved, borderline and not-assessable sentences; the card for `no_qualifying_pair`; the strip and badges in the Inspector; and a CSS test of the heatmap's `flex-shrink` if the CSS tests allow it.
- The spec: `ps_view.cluster_table` and `validation_card` are rewritten, the Validate button moves into `inspector()`, and `selection_text.subsample_sentences` gets the combined lists.

## Comments

- 2026-11-04, from [What is the bg wording of the validation card and the Inspector's Validation section?](11-bg-wording-card-and-inspector.md): the Cluster list's **Size column is 44 px** in both the wide and narrow-fit grids (was 34 / 30 px). The bg header "Размер" (39 px) overflowed it. The prototype is updated, and fit is re-verified in both languages at all four widths.
