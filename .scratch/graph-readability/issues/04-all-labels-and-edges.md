# 04: Every label shown, and lighter edges

**What to build:** every visible tag's label is drawn at a readable, constant size, and edges no longer crowd the centre.

**Blocked by:** 03

**Status:** ready-for-agent

Spec: [Graph readability spec](../spec.md): "Labels and edges".

- [ ] Every visible tag's label is drawn at a constant 11.5 px on screen at any zoom. The 6.5-unit label size and the 7 px hiding rule are gone.
- [ ] Collision culling keeps its rank (the selection and its neighbours, never hidden; then Centers; then `n_games`). It only acts once the view is zoomed out past the fit, or when a large set cannot hold every label.
- [ ] Every label has a white text halo. Selected and highlighted (`hot`) labels get a solid white background box and bold weight. Cluster Centers stay bold.
- [ ] Edges are 0.4–3 px wide at a base opacity of about 0.18, drawn under every label. Inter-cluster edges in Cluster-separated mode stay fainter. A selection still highlights its links at full strength.
- [ ] Browser check on the real Build, Global layout, 1440 × 900 and 1280 × 800, every dataset's default state: every label is shown at the first fit, none overlaps, and selecting a tag in the centre highlights its links clearly. Describe screenshots in the comments.
