# Spec: Graph interaction performance

**Status:** ready-for-agent

Synthesised on 2026-10-07 from the interaction-performance work that followed the [Graph readability spec](../graph-readability/spec.md) on the `graph-readability` branch. Glossary: [CONTEXT.md](../../CONTEXT.md). Decision record that still applies: [ADR 0002](../../docs/adr/0002-layout-is-downstream-of-analysis.md) (layout is downstream of analysis).

Most of the decisions below are already in place on the `graph-readability` branch: commits `d352029`, `578e267`, `19d62f7`, `d0b6de8` and `e5ebd0b`. This spec records them, so later changes keep them. It also adds what is still open: the browser test seam, frame-rate checks in a real browser, and the budgets that are tight or missed.

## Problem Statement

In the Tag Network Workbench, the graph reads well, but using it felt slow and unpolished:

- Selecting a tag, especially going from one well-linked tag to another (40–50 links), took one to several seconds to show the highlight and the Inspector.
- Hiding the Inspector made the floating Inspector card render 34 px wide against the right edge, and the graph re-laid itself out every time the card opened or closed.
- Zooming with the mouse wheel was sluggish.
- The animations around a selection (the pulse on the selected tag, the view sliding to show a covered tag) ran at a low frame rate and looked choppy.

A researcher clicks through dozens of tags in a session. Every click paid these costs, which made the tool tiring to explore even though no analytical number was ever involved.

## Solution

Selecting a tag is a lightweight visual interaction:

- The tap is drawn on the graph at once, within one frame. A short ring marks the selected tag.
- The Inspector fills in about a tenth of a second later. Until then its old content fades slightly, so the wait is visible but never intrusive.
- Nothing analytical runs on a selection: no Network State recomputation, no layout.
- The floating Inspector is a proper card over the right of the graph. Opening or closing it never moves the graph. If it covers the selected tag, the view slides just far enough to show it.
- Wheel zooming stays fluid: labels follow the graph during the gesture and settle at their readable 11.5 px when it ends.
- Browser-side behaviour is guarded by automated tests in a real headless browser, next to the existing callback tests. Regressions in latency, re-layouts or stale highlights fail the test suite instead of being found by hand.

## User Stories

1. As a researcher, I want a tapped tag highlighted immediately, so that the graph feels like it responds to my hand rather than to a server.
2. As a researcher, I want the highlight to appear just as fast for a tag with 48 links as for a tag with none, so that the most interesting tags are not the slowest to inspect.
3. As a researcher, I want switching from one well-linked tag to another to be as fast as the first selection, so that comparing hubs does not cost seconds per click.
4. As a researcher, I want a short, subtle mark on the tag I selected, so that I can see which node I picked among its highlighted neighbours.
5. As a researcher, I want that mark to stay smooth even while the app is busy filling the Inspector, so that the interface never looks like it stutters.
6. As a researcher, I want the Inspector's previous content to fade slightly while the new tag's content is on its way, so that I never mistake the old tag's numbers for the new one's.
7. As a researcher, I want no visible flicker when the Inspector answers quickly, so that fast responses look instant.
8. As a researcher, I want no spinner or long loading animation on a selection, so that a short wait does not feel like a long one.
9. As a researcher, I want the Inspector for a tag to arrive in a fraction of a second, so that I can read its games and connected tags without waiting.
10. As a researcher, I want tapping two tags in quick succession to end on the second one without flashing back to the first, so that fast exploration is not confusing.
11. As a researcher, I want tapping the background to clear the selection at once, so that I can return to the full graph quickly.
12. As a researcher, I want clicking a cluster's region title to highlight its members at once, so that cluster browsing is as quick as tag browsing.
13. As a researcher, I want selecting a tag from the search, the tables or the legend to behave as before, so that every entry point still works.
14. As a researcher, I want a connected tag's row in the Inspector to select its link and centre the view on it, so that I can follow links from the Inspector.
15. As a keyboard user, I want Enter or Space on a focused connected-tag row to select its link, so that the Inspector works without a mouse.
16. As a researcher, I want a selection never to recompute clusters, metrics or the layout, so that clicking around can never change a result or the picture.
17. As a researcher with the Inspector panel hidden, I want the floating Inspector card to appear at its full width over the right of the graph, so that it is readable.
18. As a researcher with the Inspector panel hidden, I want the graph not to move or re-draw when the card opens or closes, so that my view stays where I left it.
19. As a researcher, I want the view to slide just far enough to show the selected tag when the card covers it, so that I never select something I cannot see.
20. As a researcher, I want that slide to wait until the Inspector has filled in, so that it runs smoothly instead of competing with the update.
21. As a researcher, I want the slide also to happen when the card is already open and I select another covered tag, so that the behaviour is consistent.
22. As a researcher on a medium-width window (1024–1279 px), I want the floating card to sit inside the graph area at full width, so that the narrower form works as well as the wide one.
23. As a researcher, I want opening or closing a docked panel to trigger at most one new layout once the panel has finished moving, so that panel animations do not queue up several slow layouts.
24. As a researcher, I want re-opening a panel I just closed (or switching back to a layout I just used) to redraw instantly, so that toggling panels costs nothing.
25. As a researcher, I want wheel zooming to stay fluid, so that I can move between the overview and a detail without stutter.
26. As a researcher, I want every label back at its readable 11.5 px as soon as I stop zooming, so that the readability goal still holds after each gesture.
27. As a researcher who prefers reduced motion, I want no ring, fade or slide animation, so that the interface respects my system setting.
28. As a researcher, I want the Inspector's long lists (a tag's games, its connected tags, a link's games, a cluster's members, the metrics) to look exactly as before, so that the speed-up changes nothing I read.
29. As a researcher, I want every name in the Inspector shown literally, even if a game or tag name contains HTML characters, so that nothing in the data can inject markup.
30. As a researcher, I want the Inspector to keep working after the app's server restarts while my page stays open, so that a restart never breaks inspection.
31. As a researcher, I want the 250-tag loosest network to lay out within its 1.5 s budget with room to spare, so that loose thresholds stay usable on slower machines.
32. As a researcher, I want switching to the Cluster-separated layout to respond within the same 300 ms budget as the Global layout, so that the second layout is not a slow corner of the app.
33. As a researcher, I want selection, card and zoom behaviour verified in a real browser by automated tests, so that a later change cannot quietly bring the lag back.
34. As a developer, I want the browser tests to report the selection latency, the Inspector time and the longest main-thread stall, so that a regression shows up as a number, not a feeling.
35. As a developer, I want the browser tests marked slow and kept out of the default quick run, so that everyday test runs stay fast.
36. As a developer, I want a hook to drive the canvas in a page that is not being painted (refresh the size, settle animations), so that tests and checks do not depend on the window being visible.

## Implementation Decisions

### Selection is drawn at the tap (in place)
- The canvas draws a tapped node, link or cluster title at once, then sends the tap to the server. The server still decides the selection and fills the Inspector.
- The server's answer for a selection already drawn changes nothing on the canvas and is not re-applied. An answer for an earlier tap than the last one drawn is stale and is dropped: the canvas keeps a short list of locally drawn selections not yet confirmed.
- Selections from other entry points (search, tables, legend, the Inspector's connected-tag rows) keep their existing server path; the connected-tag rows also draw at once.
- A selection never asks for a layout or any analysis. The layout input does not include the selection, and the server's layout memo is keyed without it.

### Selection feedback (in place)
- The selected tag gets a ring: a DOM element over the canvas that CSS animates for 320 ms (transform and opacity only). The compositor runs it, so it stays smooth while the main thread is busy. The canvas does not redraw for it, and it is removed when the view moves.
- The style cross-fade on graph elements is gone. It never ran: a duration meant in seconds was read as milliseconds. Highlighting is instant by design.
- While the Inspector waits for its new content, it carries a pending state:
  - its old content fades to about half opacity, after a 60 ms delay so a quick answer never flickers;
  - a floating card opens at once where the Inspector is not docked;
  - any change of its content ends the state, with a 3 s fail-safe.
- Under reduced motion there is no ring and no fade transition.

### The floating Inspector (in place)
- The floating Inspector is a transient overlay of the graph. It is excluded from the canvas size reported to the server and from fits. Opening or closing it never re-lays out or refits the graph.
- As a floating card it spans the whole body grid. Its own grid column is empty (0 px) while it floats, which squeezed it to 34 px before.
- When the card covers the selected tag, the view slides horizontally just far enough to clear the card's edge. The slide starts once the Inspector's content has landed, including when the card was already open.

### Canvas reports and layout memo (in place)
- The canvas reports its size only after it has stayed the same for 150 ms, so a panel animation produces one layout request.
- The server keeps a small memo of recent layouts (12), keyed on everything the layout reads, never on the selection. It is a pure function, so the server stays stateless in effect.

### Zoom (in place)
- Label sizes and label culling run once a zoom has settled (120 ms after the last zoom event), not on every frame. A new font size makes every label redraw from scratch, about twice the cost of a frame.
- Label sizes are re-applied only when the zoom or the set of elements changed. A new selection only re-culls.

### The Inspector (in place)
- The Inspector request names the state instead of uploading its tables (about 1.8 KB instead of 123 KB). The server keeps the tables of the four most recent states by `state_id` and recomputes them from the state key when missing.
- Long lists are each one element of server-escaped HTML, which the page sets as the element's content in one step. Dash's renderer cost grows faster than the number of components it mounts, so this replaced several hundred components per well-linked tag. Markdown parsing is avoided for the same reason.
- Connected-tag rows carry their link id. One delegated click and keyboard handler sends the same event as tapping the link in the graph, with a request to centre on it. The pattern-matching inputs for these rows are gone.
- Page arrangement (block order and visibility, root classes) no longer depends on the selection. Only the Inspector's form (docked, or a floating card with a selection) follows it, in its own small callback.

### Layout speed (in place)
- The label-aware overlap pass spreads early when 25 rounds cut the total overlap by less than 10 %, instead of running jammed rounds to their limit.
- Cluster subgraphs are read once as plain graphs.
- The Cluster-separated layout is computed only when it is shown.

### Still open
- **Browser test seam.** A new development dependency for a headless browser drives the served app on a test Build (see Testing Decisions).
- **Cluster-separated time.** On the real Build, the Global layout alone takes 100–170 ms per default state. With the Cluster-separated layout (which starts from it), it takes 230–500 ms, over the 300 ms budget. The region passes are the main cost (a full zoom search re-lays out every region per attempt). Options to weigh: reuse each region's shape across zoom attempts, and start the search closer to the final zoom.
- **The 250-tag budget.** The layout takes about 1.37 s against its 1.5 s budget on the development machine; it was over the budget on a slower day. It needs headroom, not a looser test.
- **The stall at the tap with panels docked.** In a narrow canvas where labels are culled, a tap still blocks the main thread for about 25–35 ms: about 10 ms of class changes on every element, the rest culling. Options: change only the elements whose state changes, and cache node boxes between culls while positions are unchanged.
- **The `select` round trip.** The Inspector waits for the server's `select` callback before its own request starts. Making the mapping from canvas events to a selection run in the browser would save one round trip (about 20–40 ms) for every Inspector.

## Testing Decisions

- A good test drives the app the way a researcher does and checks what they would see: what is highlighted, what the Inspector shows, whether the graph moved, how long it took. It never asserts on internal functions or private state when a visible outcome exists. Timing assertions use budgets with clear headroom and report the measured number in their failure message.
- **Seam 1: the app's callbacks as plain functions (existing).** This keeps covering server behaviour:
  - a layout already made for the same inputs is not computed again, and the selection is not a layout input;
  - the Inspector needs only the state's id and recomputes tables when the memo is empty;
  - the Inspector stays a few components however many games and links a tag has;
  - Inspector names are escaped, and connected-tag rows carry their link;
  - the floating Inspector is marked as a transient overlay;
  - page arrangement does not listen to the selection.

  Prior art: the `tests/test_app.py` callback tests, including `test_a_layout_already_made_for_these_inputs_is_not_computed_again` and `test_the_inspector_stays_a_few_components_however_many_games_and_links_a_tag_has`.
- **Seam 2: the served app in a real headless browser (new, the single new seam).** It is placed at the highest point: the whole app served from a test Build, driven through clicks and wheel events. Tests, marked `slow`:
  - tap the best-linked tag, then the next: the highlight is drawn within 50 ms of the tap event, the Inspector shows the tag within 300 ms, and no layout request is sent;
  - two taps within 20 ms end on the second tag, with no frame showing the first after the second;
  - with the Inspector hidden, selecting opens a card at least 300 px wide inside the graph stage, and deselecting closes it, with no layout request and no change of the graph's viewport;
  - a tag under the card is revealed after the Inspector content lands, including when the card was already open;
  - after a tap, the longest main-thread block in the next 400 ms is at most 60 ms, and frame intervals during the 320 ms ring stay at 33 ms or less at the 95th percentile;
  - wheel zooming: no label restyle during the gesture, and every label is at 11.5 px within 200 ms after it ends;
  - toggling a docked panel sends one layout request, and toggling it back sends none (memo);
  - reduced motion: no ring element and no fade transition;
  - a connected-tag row selects its link by click and by Enter.

  Prior art: the manual browser checks recorded in the comments of graph-readability issues 03–06, and the session's in-page measurement helpers (request timing, main-thread block tracing, settling animations). The tests reuse the `tagGraph.refresh()` hook so they do not depend on the window being painted.
- **Layout timing (existing seam: layout functions).** `tests/test_layout.py` keeps the 300 ms default and 1.5 s large-network budgets. It gains a Cluster-separated budget once the open item is done.

## Out of Scope

- Any change to clustering, metrics, the Network State, `state_id`, the export schema or the layout's geometry goals (the Graph readability spec owns those).
- Replacing Dash or Cytoscape.js, WebGL rendering, and continuous physics.
- Rendering the Inspector entirely in the browser without the server.
- Server-side push (websockets) and multiple concurrent users.
- Performance of the Analysis Report mode and of the Build pipeline.
- Removal Sensitivity jobs and their progress reporting.

## Further Notes

- Measurements behind the decisions, on Build `20261006T062622Z-7a23ae9f`, 1440 × 900, Overall default state:

  | Measure | Before | After |
  | --- | --- | --- |
  | Highlight after a tap | 0.1–0.14 s; 1.4–2.0 s between hubs | 11–27 ms, drawn at the tap |
  | Inspector shown | 1.4–2.0 s between hubs | 0.12–0.18 s |
  | Inspector request upload | 123 KB | 1.8 KB |
  | Hub Inspector size | about 270 components | about 30 |
  | Longest main-thread block after a tap | 50–100 ms | 25–40 ms (one 80 ms) |
  | Wheel zoom frame | about 28 ms | about 8 ms |
  | Large-network layout | 1.57 s | 1.37 s |

  Before the wheel zoom change, each frame paid 18 ms for a redraw with new label sizes plus 8–10 ms of sizing and culling. After it, a frame is a plain redraw.
- All browser measurements so far were taken in a page that was not being painted: it was in the background, so rendering, animations and ResizeObserver callbacks were paused. Frame rates were therefore inferred from main-thread blocking, not observed. The new browser seam must run with painting active (a headless browser renders normally), and its first run should confirm or correct the frame budgets above.
- Canvas sizes are reported in 8 % steps from the reference canvas (1116 × 678), with about 1 % slack, as decided in the Graph readability spec.
