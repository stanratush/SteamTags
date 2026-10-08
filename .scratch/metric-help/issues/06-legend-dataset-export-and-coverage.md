# 06: Legend, dataset summary, Export and full coverage

**What to build:** the graph legend, the dataset summary and the Export panel get the two-layer help. The coverage test then checks every surface, and the guide's own description of help is updated.

**Blocked by:** 02, 03, 04, 05

**Status:** done

Spec: [Metric help spec](../spec.md): "Legend", "Tests", "Documentation".

- [x] `02-app-controls.md` gains `## Reading the graph`: node size (games), edge thickness (shared games), cluster colour, grey One-Tag Clusters, each with an In short.
- [x] The legend gets a "Key" label with the help. Cluster chips still select their cluster. The One-Tag chip carries its own help.
- [x] The dataset summary and Export items carry help where they show a metric or an analytical choice.
- [x] One coverage test lists every help key in the app and checks it resolves to an entry with an In short and `*Why it matters here.*`.
- [x] Getting started, the guide README and "How to read this chapter" describe the two layers, as the spec's "Documentation" section says.
- [x] All tests pass.

## Comments

- 2026-10-08: Done. `02-app-controls.md` gains `## Reading the graph` (In short and *Why it matters here.* for the section and for Node size, Edge thickness, Cluster colour and Grey One-Tag Clusters, each with an example). The legend starts with a dotted "Key" that opens the section; cluster chips still select their cluster; the one-tag chip opens Grey One-Tag Clusters. The dataset summary (Analysis Report §1's Network State table, `view.state_table`) gives both help layers to the rows that show a metric or an analytical choice (games after the filter, the thresholds, hidden and removed tags, weight, algorithm, γ, seed, R, K), with "Field: <key field>" as the tooltip's last line; Dataset and Build and Method version keep their title. The Export summary starts with a dotted "Export" that opens Deposit the export zip in `05-citing-and-reproducing.md`, which got an In short and *Why it matters here.*. One coverage test walks the layout, every recompute output and an Inspector list of every label, and checks that every help key and every Inspector label is on the page and that every help target opens an entry with In short and Why it matters. Getting started, the guide README and "How to read this chapter" describe the two layers and Back. After the two-axis review: node size follows the Minimum Months Filter and has an 18 px floor (not proportional to games); the 16 colours repeat from C17; link widths are at 100 % zoom; glossary terms instead of "group"; the Hidden tags row's entry now links to Hide defining tag; the Export help sits on a dotted word, not the whole sentence; and the Network size tooltip's "states" became "Network States". Checked in the browser: Key, one-tag chip, a cluster chip (still selects), the dataset summary rows and the Export summary, in the Workbench and Analysis Report mode.
