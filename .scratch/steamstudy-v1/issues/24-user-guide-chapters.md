# 24: User Guide: rules, app, files, citing, limitations, appendices

**What to build:** Everything in the User Guide except the metric reference, written for a researcher without network-analysis training against the real app and column names:
- the three rules;
- getting started;
- the control reference and task recipes;
- the per-file paragraphs;
- citing and reproducing a Network State;
- the full Known limitations chapter;
- the appendix on published rules of thumb;
- the references, limited to verified sources.

**Blocked by:** 23

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "User Guide and Running Guide" (outline, Known limitations, Appendices A and C).

- [ ] Chapter 0 states the three rules: no number shows a cause; clusters carry no meaning; quote the `state_id` with every network number.
- [ ] Chapter 1 covers opening the app, loading a dataset, and the two modes.
- [ ] Chapter 2 has a control-by-control table (what it does, range/default, the Network State field it sets, which numbers change) and 4–5 task recipes. No screenshots.
- [ ] Chapter 4 has one paragraph per file (what one row is, what it joins to, what it is for) for every file the schema declares, plus `snapshot.json`, `build.json`, `export.json` and `analysis.json`. The ticket 23 test passes.
- [ ] Chapter 5 covers quoting the `state_id`, depositing the zip, citing the software version, and reopening with Open Network State.
- [ ] Chapter 6 holds the full Known limitations list from the spec, and is its single home.
- [ ] Appendix A lists each published band with its source and why it does not apply here. The Steinley 2004 ARI band is left out.
- [ ] Appendix C cites only the sources confirmed in the citation-verification ticket (30 in the wayfinding effort), with the replacements and corrections the spec lists. Kaufman & Rousseeuw 1990, Steinley 2004, Rousseeuw 1987, Hubert & Arabie 1985 and Shiffler 1988 are not cited.
- [ ] The guide links to the Running Guide in one line. "Operator" means only the Steam Charts site operator. Domain terms follow the glossary.
