# 08: In short and Why it matters for the remaining guide entries

**What to build:** the guide entries the app does not link to (ranking and data, feature analysis, Build diagnostics) get the same In short block and `*Why it matters here.*` paragraph, so the whole guide reads the same way.

**Blocked by:** 07

**Status:** done

Spec: [Metric help spec](../spec.md): "Out of scope".

- [x] Every `###` entry in `03-metric-reference.md` has an In short block and `*Why it matters here.*`.
- [x] The guide test requires both for every entry, not only the ones the app links to.

## Comments

- 2026-10-08: Done (taken up at the researcher's request to continue). The 32 remaining `###` entries of `03-metric-reference.md` (14 in Ranking and data, 17 in Feature analysis, and the Resolution Sweep) gained an In short block and a *Why it matters here.* paragraph, written to the content rules (study framing "the most-played games", glossary terms, no quality words, at most 60 words) and checked against each entry's own text. "How to read this chapter" now says every entry has both. `test_every_metric_entry_opens_with_in_short_and_says_why_it_matters` requires both for every entry; the existing form and banned-word tests cover the new blocks. The app is unchanged: these entries are reached through links inside the help and the panel `?` sections.
