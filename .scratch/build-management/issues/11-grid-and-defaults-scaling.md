# Do the Parameter Grid and network defaults scale with list size and tags per game?
Type: grilling
Status: resolved
Blocked by: 05

## Question

The Parameter Grid (g 3–20, s 2–12), the network defaults (g = s = 8), `min_support = 10` and the Null Comparison and Subsample Stability settings were set for 100 games with up to 20 tags each. Now that [list size and tags per game](05-tags-per-game-and-list-size.md) are settings, a Top-300 at 10 tags per game gives a very different network.

Decide:
- whether the grid ranges and defaults stay fixed (the user edits them in the menu's network section), scale with list size, or are bounded by a rule;
- what the menu warns about, e.g. a grid whose largest g exceeds what the list size and tags per game allow;
- whether the Automatic Parameter Selection guide text ("tends to be higher at large g", the 80% subsample) still holds, or needs a caveat for other sizes;
- whether one-off measurements are needed before deciding (a `task` ticket on a non-default Build).

From [tags per game and list size](05-tags-per-game-and-list-size.md): list size can be as low as 10 and tags per game as low as 2 (one value per Build). Decide whether the grid needs a higher floor, or a warning, at small values.

## Answer

Settled with the researcher, 2026-11-07. No ADR: nothing is implemented yet, so the choice is cheap to reverse.

Facts that shaped it: Subsample Stability already scales with dataset size (`m = ⌊0.8 n⌋`, `g′ = ⌊g m/n⌋`, `s′ = max(2, ⌊s m/n⌋)`); the Null Comparison's shuffles keep every game's tag count and every tag's game count, so they hold at any N and tags per game; the Pair Constraints already make unusable pairs non-qualifying.

- **Fixed, absolute, one value per Build.** The Parameter Grid (`g_range`, `s_range`), the network defaults (g, s), `min_support` and the other Parameter Selection settings (Pair Constraints, R, S, `resolution_sweep`) stay game counts the user edits in the menu's network section. Nothing scales with list size or tags per game: scaling would change what g means between Builds, every cache key and every Parameter Selection export. One value serves every dataset of the Build.
- **Warnings, per dataset, never a refusal.** The Build menu warns, naming the dataset and its N, when the grid's largest g exceeds N (those pairs have no network), when the network default g or s exceeds N (the default view opens empty), or when `min_support` exceeds N (`combinations.csv` and `associations.csv` are empty). Saving stays allowed. Each warning gets a bg entry.
- **A grid with no pairs is refused** (s_low > g_high leaves no pair with s ≤ g), by both the menu and the config reader, with a bg error. Today this goes unchecked.
- **No higher floor.** List size ≥ 10 and tags per game ≥ 2 stand ([tags per game and list size](05-tags-per-game-and-list-size.md)); no grid floor and no warning tied to tags per game. A small Build with no Qualifying Pair shows today's "no qualifying pair" result.
- **Network State sliders** keep 1–40 (g) and 1–30 (s), raised only to the Build's own largest configured value (its network default or the top of its grid range). Default Steam Builds are unchanged; a bound that follows N would make the Top-100 slider too coarse.
- **Guide text holds.** "Tends to be higher at large g" is about step size relative to the network and holds at any size; the 80% subsample already scales. One caveat sentence (with a bg entry) joins the Automatic Parameter Selection guide section: the default Parameter Grid and network defaults were chosen for a Top-100 at 20 tags per game; for other list sizes or tags per game, review them in the Build menu.
- **No measurement ticket:** with nothing scaled, no decision waits on a number.
- **Glossary:** Parameter Grid now says the ranges are set per Build, with today's values as the default.

