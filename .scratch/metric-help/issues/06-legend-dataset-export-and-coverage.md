# 06: Legend, dataset summary, Export and full coverage

**What to build:** the graph legend, the dataset summary and the Export panel get the two-layer help. The coverage test then checks every surface, and the guide's own description of help is updated.

**Blocked by:** 02, 03, 04, 05

**Status:** ready-for-agent

Spec: [Metric help spec](../spec.md): "Legend", "Tests", "Documentation".

- [ ] `02-app-controls.md` gains `## Reading the graph`: node size (games), edge thickness (shared games), cluster colour, grey One-Tag Clusters, each with an In short.
- [ ] The legend gets a "Key" label with the help. Cluster chips still select their cluster. The One-Tag chip carries its own help.
- [ ] The dataset summary and Export items carry help where they show a metric or an analytical choice.
- [ ] One coverage test lists every help key in the app and checks it resolves to an entry with an In short and `*Why it matters here.*`.
- [ ] Getting started, the guide README and "How to read this chapter" describe the two layers, as the spec's "Documentation" section says.
- [ ] All tests pass.

## Comments
