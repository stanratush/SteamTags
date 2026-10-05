# 22: Feature-analysis report

**What to build:** Every Build renders `analysis/report.html`: a templated, non-causal report with one section per dataset. Every number comes from the analysis CSVs. Each section has:
- the frequency headlines against the Eligible Pool;
- the cluster list with centers;
- Q vs null;
- the seed-stability sentence with the least stable tags;
- the Resolution Sweep sentence;
- the Removal Sensitivity sentence with its expected-chance wording.

The report opens with a caveat paragraph, has a methods section, ends with a fixed limitations paragraph, and fails the Build if any causal word appears.

**Blocked by:** 09, 13, 15, 20, 21

**Status:** done

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Feature analysis" (Report).

- [x] It is built only from fixed sentence templates through the templating and causal-word component from ticket 09. Every number is read from the Build's CSVs or `analysis.json`.
- [x] It opens with the standard caveat paragraph: q-values are a descriptive screen, and the Top 100 is not a random sample. Significance is never mentioned.
- [x] Per dataset:
  - the `months_observed` distribution and the `is_free` count;
  - templated frequency sentences, with genre headlines from `kind = genre` rows only and the Puzzle note;
  - Content Flag counts;
  - the cluster list (labels, members, `center`, `center_medoid_score`, `top_strength_tag`, `center_is_top_strength`);
  - the Q-vs-null line;
  - the stability sentence, plus the bottom-5 Membership Stability tags (or all tags below 1.0 if fewer);
  - the Resolution Sweep sentence, never comparing Q across γ;
  - the Removal Sensitivity sentence (count and names of flagged tags, and "at most about n/(K+1)" expected by chance).
- [x] The methods section covers every element the spec lists, including the disconnected-cluster count and "no consensus partition".
- [x] It ends with the fixed limitations paragraph (snapshot tags; ranked selection, not a sample; single clustering run; Steam Charts gaps), linking to User Guide chapter 6.
- [x] Tests: a template with a causal word fails the Build, and sampled numbers in the rendered report match the CSV values.

## Comments

- 2026-10-04 (agent): Implemented: analysis/report.py renders analysis/report.html from templates only (caveat, per-dataset sections, methods, limitations linking to docs/user-guide/06-known-limitations.md). The report never mentions significance; the removal sentence calls the flag a screening aid. A causal word fails the Build.
- 2026-10-05 (agent, audit): Audit: every criterion checked against the code and tests; all met.
