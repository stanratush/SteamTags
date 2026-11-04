# 17: Card and report sentences, in English and Bulgarian

**What to build:** `selection_text`'s validation sentences say what the new summary says: the Null Comparison in its three states over D, with the scope header, U's reasons, the weak warning, the observed-runs note, the Multi-Tag Cluster line and the width sentence; Subsample Stability with labelled ARI spreads, one combined dissolved list, the borderline and not-assessable sentences and the limitation sentence. Every string has its Bulgarian, the retired keys go, and the golden texts are regenerated. The card's widgets come in issue 18.

**Blocked by:** 16

**Status:** ready-for-agent

Spec: [Validation review spec](../spec.md): "The card" items 2–4 and 6, "Bulgarian", "Tests". Verbatim English and Bulgarian: [bg-strings.md](../prototypes/11-bg-wording/bg-strings.md) ("Card" table) and the observed-runs note in [What do the User Guide's validation passages … say?](13-guide-and-context-wording.md), point 2. Sources: tickets [02](02-cluster-figures-and-verdict.md), [04](04-null-comparison-rule-and-wording.md), [06](06-validation-card-and-inspector-layout.md), [11](11-bg-wording-card-and-inspector.md).

- [ ] **`null_sentences`:**
  - header "({r} shuffled networks, per-pair procedure at g = {g}, s = {s})";
  - "Q at resolution … is …;" then the state's sentence: "none of the {d} shuffled networks with a Q reaches it (range over {d} shuffled networks: {lo} to {hi})" / "{k} of {d} shuffled networks with a Q reach it: Q not above the null" / "no shuffled network has edges, so Q cannot be compared." (edgeless only) or the reasons form;
  - U's reasons appended when U > 0 ("{n} had no edges", "{n} lay beyond their γ scan");
  - the observed-runs note when `q.observed_from_runs`;
  - the weak warning when `weak`;
  - "Multi-Tag Clusters: observed {o}, median {m} (range over {k} shuffled networks with a Selected Partition: {lo} to {hi})." or "None of the {r} shuffled networks has a Selected Partition.";
  - "Median domain width {m} vs observed {o}; observed wider than {n} of {k}.", both `.3f`, with "equal to {t}," only when ties exist;
  - "Widths are upper bounds, conditional on the partitions the γ scan finds.", then `NULL_CAVEAT`.
- [ ] **`subsample_sentences`:**
  - "Re-selected: median ARI {m} (10th–90th percentile: {lo} to {hi}) over {n} of {t} subsamples, on {e} of the tags." with degenerate reasons as today (including `beyond_scan` for the at-resolution arm), then "At resolution {res}: median ARI …";
  - the combined dissolved list: the one-key lead (the template bolds the text before the first " ("), "{k} of {n} Multi-Tag Clusters in both arms" (`tx.n` on `{n}`), "re-selected only", "at resolution only", empty groups left out;
  - "Borderline (the 95% Wilson interval contains ½): … in both arms / …";
  - "Not assessable (fewer than 2 of its tags survive in every subsample): …";
  - "No Multi-Tag Cluster is dissolved in most subsamples in either arm." only when nothing is labelled and nothing is not assessable;
  - `SUBSAMPLE_CAVEAT` and the limitation sentence, in italics.
- [ ] Numbers: `.3f` for Q and widths, `.2f` for ARI; the decimal comma in bg; ARI ranges always "от … до"; the minus sign `−`.
- [ ] **Catalogue:** every new key in `i18n/bg/selection_text.py`, with bg-strings.md's Bulgarian; the retired `selection_text` keys listed in the spec are removed. Existing placeholder names are kept where an entry already exists.
- [ ] **Golden texts:** `test_validation_block_golden_text` and `tests/fixtures/selection_report_{en,bg}.md` are regenerated with `STEAMSTUDY_WRITE_GOLDEN`. Comments quote the diff's key lines: the unlabelled ranges and the "wider"/"narrower" wording are gone.
- [ ] Render tests: each null state; the weak warning; U reasons; the observed-runs note; the combined list with all three groups and with one; the "no Cluster dissolved" sentence suppressed by a not-assessable Cluster.
- [ ] The catalogue parity test and the full test suite pass.
