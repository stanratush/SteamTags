# Do the Parameter Grid and network defaults scale with list size and tags per game?
Type: grilling
Status: open
Blocked by: 05

## Question

The Parameter Grid (g 3–20, s 2–12), the network defaults (g = s = 8), `min_support = 10` and the Null Comparison and Subsample Stability settings were set for 100 games with up to 20 tags each. Now that [list size and tags per game](05-tags-per-game-and-list-size.md) are settings, a Top-300 at 10 tags per game gives a very different network.

Decide:
- whether the grid ranges and defaults stay fixed (the user edits them in the menu's network section), scale with list size, or are bounded by a rule;
- what the menu warns about, e.g. a grid whose largest g exceeds what the list size and tags per game allow;
- whether the Automatic Parameter Selection guide text ("tends to be higher at large g", the 80% subsample) still holds, or needs a caveat for other sizes;
- whether one-off measurements are needed before deciding (a `task` ticket on a non-default Build).
