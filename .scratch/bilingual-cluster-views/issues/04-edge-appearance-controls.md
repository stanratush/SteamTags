# Edge appearance controls
Type: prototype
Status: open
Blocked by: none

## Question

What edge appearance controls does the Workbench offer, and how do they look and behave? This is a HITL prototype (`prototype`, in `prototypes/04-edge-appearance/`).

- Today: width = 0.4 + 2.6 × value / the network's largest value (`renderer.payload`), measure from the Clustering Weight or the "show shared games" switch ([Edge thickness follows the Clustering Weight](../../edge-thickness/issues/01-thickness-follows-clustering-weight.md)), with intra/inter, dim, neighbour and selected opacities in `graph.js`.
- Candidate controls: width range (minimum and maximum), scaling (linear, square root, log, rank), colour (one neutral, by Cluster, intra vs inter, a gradient by value), opacity (overall, inter-cluster edges in the separated layout), and possibly a "hide edges below value" view filter. That filter must not be confused with Minimum shared games, which is part of the Network State.
- The defaults reproduce today's look exactly. All of it is a view choice: never part of the Network State, an export or any number. Does it reset with Reset, persist per browser, or apply per layout?
- Legend and help: how the legend says what is drawn and how it is scaled. Does each control get a guide entry?
- Performance budgets from the [Graph interaction spec](../../graph-interaction/spec.md): changing a control must not relayout or re-send the graph.
