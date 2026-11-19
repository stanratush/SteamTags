# 03: Cluster Comparison: Left and Right dataset dropdowns

**What to build:** two dropdowns above the diagram choose which dataset is on each side.

**Blocked by:** 02 (same pair header row)

**Status:** done

Spec: [UI Declutter spec](../spec.md): "Choosing the pair", "Docs". Code: `src/steamstudy/app/cc_view.py` (`pair_block`, `chosen_pair`, `oriented`, `pair_rows`), the `cc-pair` and `cc-orient` stores, `callbacks.py`.

- [x] The pair title "A × B ⇄" is replaced by Left [▾] ⇄ Right [▾]. Each dropdown lists the included datasets only, names in their dataset colours, not clearable.
- [x] Left and Right set the shown pair and its orientation (Left = column A of the diagram). ⇄ swaps the two dropdowns' values.
- [x] Picking on one side the dataset on the other side swaps the sides.
- [x] Unticking the dataset on a side moves that side to the remaining included dataset with the highest ARI against the other side. With fewer than two included datasets the pair view hides as today.
- [x] Clicking a row in Dataset pairs sets Left to its A and Right to its B. The row of the shown pair is highlighted whichever way round it is shown.
- [x] Focus, match and "show weaker" view choices behave as today when the pair changes.
- [x] Every new string has a bg entry; the help entry for the swap still opens.
- [x] User Guide `02-app-controls.md` (en and bg) describes choosing sides.
- [x] Tests (`tests/test_cc_app.py`, pure functions in `cc_view`): same-side pick swaps; untick fallback picks the highest ARI; dropdown options follow the included datasets; a pair-row click sets both sides.

## Comments

**2026-11-19, implementation.** `cc-pair` now holds the sides asked for, [left, right]. `cc_view.chosen_sides` gives the pair shown and its sides: both wanted datasets included gives those sides; one unticked keeps the other on its side and gives the free side the highest-ARI partner; otherwise the top pair, its earlier dataset on the left. `shown["sides"]` is what `cc_main` draws, and `cc-orient` is gone. One callback, `cc_sides`, takes Left, Right, ⇄ and the pair rows (the dropdowns are both its inputs and outputs) and reads every changed prop, not only `triggered_id`: a render can change the dropdowns and re-render the rows at once. When the sides shown differ from those asked for (the first render, an untick), `cc_render` sets the dropdowns with `set_props`. They cannot be declared Outputs, since they feed `cc-pair`, which it reads. The options travel with the value, because a dropdown clears a value its options do not hold yet: that was the first browser run's bug, empty dropdowns. The title span (`cc-title`, `MainView.title`) is gone: the dropdowns are the title.

Checked in the browser at 1440×900: the first render fills Overall ⇄ RPG and records it. Left = RPG (the right's dataset) swaps to RPG ⇄ Overall. Right = Strategy, then unticking Strategy gives RPG ⇄ Overall: RPG keeps its side, and Strategy leaves the options. ⇄ gives Overall ⇄ RPG with the columns following. Re-ticking keeps the sides. The pair-list highlight follows either way round. No callback loop: only the Build strip's timer kept polling.

