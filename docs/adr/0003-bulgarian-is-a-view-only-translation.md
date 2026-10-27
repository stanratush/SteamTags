# Bulgarian is a view-only translation, keyed by English text

The Tag Network app and its User Guide can be shown in Bulgarian, but the **Interface Language** is a view choice only. Exported files (CSV, JSON, `selection_report.md`), the CLI, the Running Guide and the release checklist stay English. Steam tag names, game titles, Genre values and Cluster labels are never translated. No Network State, `state_id`, export or cache key depends on the language.

The message catalogue is plain Python dicts **keyed by the English text** (`tx("Genre Tag hidden")`), with named placeholders and two plural forms (`one`, `other`). The language reaches the text through an explicit, required translator, `tx = text(lang)`, because one process renders both languages at once: the Parameter Selection explanations appear in the app and also go into the English `selection_report.md`. The Bulgarian guide is a parallel `docs/user-guide/bg/` copy whose headings carry explicit `{#<english-slug>}` ids, so every code reference and in-guide link stays language-independent.

We chose this over three alternatives:

- **gettext `.po`/`.mo`**: it needs a compile step and a build tool, and its plurals add nothing over two whole forms.
- **Semantic message ids**: code would stop reading as the English it shows, and the ~70 English phrase tests would have to be rekeyed.
- **A separate heading map**: a second file that drifts from the guide.

An edited English string changes its key on purpose: the catalogue parity test then fails until the Bulgarian is updated. That failure is how parity is kept.

## Consequences

- Switching is live, driven by a `lang` store. It never recomputes a Network State or interrupts a running job.
- Every function that renders visible text takes `tx`. Export and CLI callers pass `text("en")`.
- English heading text can change freely. A Bulgarian heading's id must keep the English slug it was given, and the parity tests enforce this.
- English content tests (banned words, required statements) stay English-only. Bulgarian is checked for structure by tests, and for meaning by the researcher's review.
