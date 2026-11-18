# 03: App line, User Guide and glossary

**What to build:** the read-only line in Parameter Selection mode, the User Guide paragraphs (en and bg) and the glossary term. They go in together, because `tests/test_guide.py` requires each CONTEXT.md term to appear in the guide.

**Blocked by:** 01

**Status:** ready-for-agent

Spec: [Workbench Seed Priority spec](../spec.md): "Term", "What the app shows", "User Guide". Facts for the guide: [measurement](../prototypes/01-seed-priority-effect/results.md).

- [ ] Parameter Selection's Controls column, under the Fixed settings, always shows "Workbench seed priority: Closest γ to the midpoint" or "… Prefer the main seed". It is read-only, with a help key `selection.workbench_seed_priority` if its neighbours have help icons.
- [ ] CONTEXT.md gets the **Workbench Seed Priority** entry with its _Avoid_ line (seed preference, seed mode, main-seed mode). `docs/i18n/bg-terms.md` gets the matching row.
- [ ] `docs/user-guide/02-app-controls.md` "Apply to Workbench" gets one paragraph. It describes both orders, recommends the default and explains why (γ nearest the CHAMP midpoint; the seed has no meaning of its own). It gives the measured cost of `main_seed` (92 of 667 pairs at a less central γ, a median 41% of the way to the domain's edge; no default chosen pair changed). The Seed-Noise Floor caution notes that `main_seed` doesn't make the two floors agree.
- [ ] `docs/user-guide/07-making-builds.md` "Network defaults" gets one sentence naming the key, its values and its default, linking to that paragraph.
- [ ] Chapter 3 gets an entry for the term.
- [ ] Every new string and guide paragraph has its bg form (catalogue and the Bulgarian guide copy). The bg parity tests pass.
- [ ] Tests: the line shows each value on a fixture Build with each setting. `test_guide` term coverage and the i18n parity tests pass.

## Comments
