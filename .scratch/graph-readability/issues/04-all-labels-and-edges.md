# 04: Every label shown, and lighter edges

**What to build:** every visible tag's label is drawn at a readable, constant size, and edges no longer crowd the centre.

**Blocked by:** 03

**Status:** done

Spec: [Graph readability spec](../spec.md): "Labels and edges".

- [x] Every visible tag's label is drawn at a constant 11.5 px on screen at any zoom. The 6.5-unit label size and the 7 px hiding rule are gone.
- [x] Collision culling keeps its rank (the selection and its neighbours, never hidden; then Centers; then `n_games`). It only acts once the view is zoomed out past the fit, or when a large set cannot hold every label.
- [x] Every label has a white text halo. Selected and highlighted (`hot`) labels get a solid white background box and bold weight. Cluster Centers stay bold.
- [x] Edges are 0.4–3 px wide at a base opacity of about 0.18, drawn under every label. Inter-cluster edges in Cluster-separated mode stay fainter. A selection still highlights its links at full strength.
- [x] Browser check on the real Build, Global layout, 1440 × 900 and 1280 × 800, every dataset's default state: every label is shown at the first fit, none overlaps, and selecting a tag in the centre highlights its links clearly. Describe screenshots in the comments.

## Comments

- 2026-10-07: Done. Every label is sized to 11.5 px on screen after every zoom (`sizeLabels`), with a 2 px white halo; `hot` labels (the selection and its neighbours) get a solid white box and weight 700, Centers stay at 650. `renderer.priority` ranks every tag (Centers, then `n_games`, ties by id); the `pri` class and the 15-label cut are gone. Culling runs only below max(the first-fit zoom, the zoom the layout spaced the labels for) × 0.99, so a large set laid out for 0.55 still culls at its first fit. Edges: 0.4 + 2.6 × shared / max shared (0.4–3 px at zoom 1), opacity 0.18; a selected tag's links turn #4a5262 at 0.9; inter-cluster links in Cluster-separated mode stay at 0.06.
- Browser check on the real Build `20261006T062622Z-7a23ae9f`, Global, Tables and Inspector closed, every dataset's default state. I measured with Cytoscape's own label metrics plus the 2 px halo; its `boundingBox()` pads labels by several pixels and over-counts. The pane was hidden, which pauses rendering, animations and the ResizeObserver, so the check calls the new `tagGraph.refresh()` and places nodes at their targets before measuring.

  | Dataset | 1440 × 900 (canvas 1116 × 678) | 1280 × 800 (canvas 957 × 538) |
  | --- | --- | --- |
  | Overall | 59 labels, 0 hidden, 0 overlaps, zoom 1, smallest node 27.4 px | 59, 0, 0, zoom 1, 27.4 px |
  | Puzzle | 58, 0, 0, zoom 1, 26.5 px | 58, 0, 0, zoom 1, 26.5 px |
  | RPG | 67, 0, 0, zoom 1, 26.5 px | 67, 0, 0, zoom 0.996, 26.4 px |
  | Strategy | 65, 0, 0, zoom 1, 26.5 px | 65, 0, 0, zoom 1, 26.5 px |
  | Simulation | 60, 0, 0, zoom 1, 26.5 px | 60, 0, 0, zoom 0.898, 23.8 px |

  Every label sits inside the view at 11.5 px. Screenshot (Overall, 1440 × 900): the graph fills the canvas, and every tag's name is readable under its node with a white halo over the faint grey links. Unlinked tags (Replay Value, Lore-Rich, Looter Shooter, LGBTQ+) sit just outside the main graph.
- Selection check (Simulation, 1280 × 800): tapping Multiplayer, the hub with 52 links, opens the floating Inspector. The graph re-lays out for 886 × 538 (zoom 0.72, smallest node 19.2 px). Its 52 links turn dark at 0.9 opacity, all other links fade to 0.04, the 7 unlinked tags dim, and the 53 highlighted labels are bold on white boxes: 0 overlaps. Screenshot: a clear star of dark links from Multiplayer in the centre to every neighbour, each neighbour's name bold and boxed.
