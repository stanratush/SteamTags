# Bulgarian terminology
Type: grilling
Status: open
Blocked by: none

## Question

Which Bulgarian term stands for each domain term and metric name, and how are numbers written in Bulgarian? This is a HITL grilling with the researcher (`grilling` + `domain-modeling`). The result is a term table that every translation follows.

- Every term in [CONTEXT.md](../../../CONTEXT.md): Cluster, Multi-Tag/One-Tag Cluster, Cluster Center, Tag, Genre, Genre Tag, Tag Network, Clustering Weight, Lift, Network State, Seed-Noise Floor, Membership Stability, Removal Sensitivity, Threshold Pair, Neighbour Agreement, Selected Partition, Mean Monthly Players, Observation Window, and the rest. For each: translate it, transliterate it, or keep it in English, and list the Bulgarian forms to avoid, as the glossary does.
- Metric and method names: Modularity Q, Silhouette, Coverage, conductance, ARI, Jaccard, Leiden/Louvain, resolution γ, curveball null.
- Dataset labels from `config/datasets.toml` (`Overall`, `Puzzle`, `RPG`, `Strategy`, `Simulation`). They are config data, but they read as words and also appear in exports.
- The guide's fixed labels, if [Translation mechanism](02-translation-mechanism.md) makes them per language: `In short.`, `Higher →`, `Lower →`, `Raising it →`, `Here:`, `Caution:`, `Now:`, `Column(s):`, `Why it matters here`, `Exact definition`, `Example`, `Bounds`, `Compare with`, `Shown in the app as`. Also the banned quality words (`good`, `strong`, `stable`, …) that In short blocks must avoid in Bulgarian. Inventory: [research/01-string-inventory.md](../research/01-string-inventory.md).
- Number format on screen: the decimal comma (0,42) with a space as the thousands separator, or dots everywhere, so screen values match exports and the paper. Exports stay unchanged either way (map Notes).
- Where the table lives: a Bulgarian column or section in CONTEXT.md, or a separate glossary file.
