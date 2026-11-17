# Spec: Cluster Comparison

Settled through the [Cluster Comparison map](map.md) (wayfinder, 2026-11-16 to 2026-11-17). Each decision below is the current state of its ticket, with every later amendment already applied: the final names of [What are the measures called, and how is each one read?](issues/11-names-and-readings.md) replace the working names used in earlier tickets ("Common Tags", "Lift", "no overlap", "isolated"). When this spec and a ticket's Answer disagree, the spec wins. Glossary: [CONTEXT.md](../../CONTEXT.md). Constraints: ADR 0002 (layout downstream of analysis), ADR 0003 (every string has a bg catalogue entry), ADR 0006 (one Build per tab).

## Goal

The Tag Network app gains a fourth mode, **Cluster Comparison**, beside the Workbench, Analysis Report mode and Parameter Selection. In it the user:

1. includes any number of the open Build's **Top-N Datasets**, each with its own g, s and resolution, taken by default from its **Automatic Parameter Selection** run;
2. sees every **dataset pair** ranked by ARI on their **Comparable Tags**;
3. picks one pair and sees how the **Multi-Tag Clusters** of one dataset match those of the other, as a two-column link diagram of **Cluster Matches** ranked by **Match Jaccard**;
4. opens one match: its shared and unshared Tags, its figures, and the games in both Clusters;
5. exports every pair as a record (six CSVs and `comparison.json`).

**What it never claims.** A Cluster Match says that two Clusters, each found at its dataset's settings, share Tags. It is never evidence that the Clusters are real or that the datasets share a genre structure. Similarity is computed on Tag sets only; games are shown, never scored. No figure gets wording bands, and no p-value is given.

## Facts this spec rests on

Measured on the full Build `20261005T062558Z-full/20261008T221504Z-7a23ae9f` (Lift, Leiden, no Minimum Months Filter, Genre Tags and defining Tags hidden), the only Build with an Automatic Parameter Selection run for all five datasets, unless a line says otherwise.

- **The datasets on their picks** (default Pair Constraints): Overall 29 Tags / 4 Multi-Tag Clusters, Puzzle 31 / 4, RPG 71 / 15 (plus 3 One-Tag Clusters), Strategy 39 / 3, Simulation 38 / 3. Seed-Noise Floor 1.00 for three of them, Puzzle 0.52, RPG 0.80.
- **10 pairs, 103 Cluster Matches.** Match Jaccard median 0.09, quartiles 0.06–0.16, maximum 0.58. ARI (comparable Tags) 0.07 (Puzzle × RPG, Puzzle × Simulation) to 0.53 (Strategy × Simulation). At a minimum of 0.10, 48 matches remain, 51 of the 58 one-Tag matches are hidden, 23 of 116 Clusters (per direction) still show a split; at 0.20 only 1 does ([report](prototypes/04-measures-on-real-builds/report.md)).
- **Measures:** the minimum containment correlates 0.96 with Jaccard and never changed a top match; Jaccard (comparable) gains ≥ 0.10 over Match Jaccard on 27 of 80 judged matches; Overlap vs. expected correlates 0.38 with Jaccard and would change 13 of 58 top matches, mostly towards one-Tag matches. AMI and mean best Jaccard order the pairs like ARI (Spearman 0.90, 0.84).
- **Games in common:** Overall has 1 game in common with Puzzle, 38 with RPG, 24 with Strategy, 28 with Simulation; Puzzle has at most 1–2 with any Tag-Specific Dataset. So the games list for a Puzzle pair is nearly always empty.
- **The seed:** a cell's Selected Partition is chosen by CHAMP from partitions pooled over 10 scan seeds; the Workbench seed is only an address. Using one shared seed at each cell's γ would replace the Selected Partition with a different one in about 25–55% of cells ([Why does the seed change between cells?](issues/10-seed-per-dataset.md)).
- **Defining Tags shown** (re-clustered at the picks): 9 matches rest on a defining Tag alone, one above 0.10 (RPG C14 ~ Strategy C4, 0.12); ARI falls by up to 0.06 ([What happens to a defining Tag in a match?](issues/14-defining-tag-in-a-match.md)).
- **Time:** reading one dataset's Parameter Selection cache ≈ 0.3–0.5 s; the network, one clustering and 10 noise seeds ≈ 0.07 s; a full `compute_state` ≈ 0.6–0.7 s; matching all pairs takes milliseconds. The Workbench keeps no states beyond `STATE_TABLES`.
- **This Build's cache uses 64-digit folder names**; `ps_cache.NAME_LENGTH` is 16, so the app shows its runs as "not run". The prototypes override it in memory. The mode needs no change for this; to see this Build's runs in the app, they are rerun (a fact, not a decision of this spec).
- Prototype code, reference only (never imported): [run.py](prototypes/04-measures-on-real-builds/run.py) (every measure and flag), [export.py](prototypes/06-look-of-the-mode/export.py) and [logic.js](prototypes/06-look-of-the-mode/logic.js) (matching in the browser), [index.html](prototypes/06-look-of-the-mode/index.html) `?variant=B` (the layout this spec takes).

## Decisions

### Scope

- **In:** the Dash-free comparison module, the app mode, "Use in Cluster Comparison" in Parameter Selection, the export, the glossary terms, the User Guide (en and bg), the metric reference, in-app help and the bg catalogue.
- **Out:** see [Out of scope](#out-of-scope). Most importantly, datasets of different Builds and any similarity computed on games.
- **No new dependency.** ARI uses scikit-learn's `adjusted_rand_score`, already used by `selection.link`.

### Terms

Five terms enter CONTEXT.md **with the implementation** (not before: `tests/test_guide.py` requires each to be in the User Guide), each with its Avoid line; `docs/i18n/bg-terms.md` gains a matching row.

| Term | Definition (gist) | Avoid | Bulgarian |
|---|---|---|---|
| **Cluster Comparison** | The app mode that matches the Clusters of Top-N Datasets of one Build, two at a time | cluster tracking, cross-dataset clustering | *сравнение на клъстери* |
| **Cluster Match** | Two Multi-Tag Clusters, one from each of two datasets, that share at least one Tag | correspondence, same cluster, shared cluster | *съвпадение на клъстери* (avoid *съответствие*) |
| **Comparable Tags** | The Tags in both networks of a dataset pair (visible and reaching the minimum games per tag in each; One-Tag Clusters count); the only Tags the comparison can judge a Cluster on | common Tags, surviving Tags | *сравними тагове* |
| **Match Jaccard** | The shared Tags of a Cluster Match as a share of all Tags in either Cluster | Whole-Cluster Jaccard, similarity unqualified | *индекс на Jaccard на съвпадението* |
| **Comparison State** | Everything that fixes one Cluster Comparison result; has a `comparison_id` | comparison unqualified, session, view | *състояние на сравнението* |

Display phrases, not terms: **dataset pair** · *двойка набори* (always qualified: *двойка* alone is the Threshold Pair); **shared Tags** · *общи тагове* (in both Clusters of a match); **games in both Clusters** · *игри в двата клъстера* (never "shared games", which belongs to an edge); **games in common** (ranked in both Top-N Datasets). The reserved names **Hennig's Jaccard**, **Whole-Cluster Jaccard**, **Lift** and **Connection Ratio** are never reused.

### Datasets and their values

Sources: [Where do each dataset's g, s and resolution come from?](issues/03-per-dataset-defaults.md), as amended by tickets 10 and 14.

- **Any number of the Build's Top-N Datasets** can be included; all are included when the mode first opens. Matching is always between two at a time.
- **Each dataset has a source**, one of four (export code in brackets):
  - **the pick** (`pick`): the run's starred cell under the Pair Constraints currently set in Parameter Selection for the tab (the comparison has no constraints of its own). Every dataset starts here when its run exists;
  - **a selected cell** (`cell`): another cell of the run with a Selected Partition, chosen in Parameter Selection ("Use in Cluster Comparison", below) or by typing its g and s;
  - **set by hand** (`hand`): g or s typed to a pair with no Selected Partition, or γ edited;
  - **no run** (`no_run`): no Automatic Parameter Selection run under the shared settings; starts from the Build's network g, s and resolution.
- **A dataset on a cell (pick or selected) shows the cell's stored Selected Partition.** It is read from the Parameter Selection cache, never re-clustered, and has no seed, "not reproduced" cells included. Its γ is the Selected Resolution.
- **A dataset set by hand or with no run is clustered once with the Build's main seed**, the same for every such dataset. The mode has no seed control.
- **Editing in the dataset row:** typing g and s that name a cell with a Selected Partition selects that cell (γ follows); any other pair, or editing γ, makes it "set by hand" (γ as typed). Limits on g, s and γ are the Workbench's, not the Parameter Grid's.
- **Pair Constraints changed in Parameter Selection** reach the comparison on its next resolve: a dataset on the pick follows the new pick; a selected cell or hand-set values are kept.
- **A cell that vanishes** (cache cleared, run changed) falls to the no-run rule: network defaults, and the source line says the run is gone. Old values are not kept as "set by hand".

### Shared settings

- **Shared across every dataset:** Clustering Weight, algorithm, Minimum Months Filter, the hidden Genre Tags, and the removed Tags. They are the mode's own controls, a single row in the mode's header, starting from the **Parameter Selection settings** (Leiden, Lift, its filter, its hidden Genre Tags, its removed Tags), never from the Workbench's.
- **Hidden Genre Tags** is the same chip checklist as Parameter Selection's `ps-s-genre`. **There is no defining-Tag control:** each dataset's own defining Tag is always hidden in that dataset (`hide_defining_tag` fixed on). A Parameter Selection run made with the defining Tag shown therefore never feeds the mode.
- **Changing a shared setting re-resolves every dataset** against the run for the new settings: its pick if that run exists, no run if not. Hand edits are lost, and a notice says so.

### Matching

Sources: tickets [01](issues/01-similarity-measures.md), [02](issues/02-tags-missing-from-the-other-network.md), [04](issues/04-measures-on-real-builds.md), [11](issues/11-names-and-readings.md), [14](issues/14-defining-tag-in-a-match.md).

For a dataset pair A, B, with partitions P_A and P_B:

- **Comparable Tags** C = Tags in both networks. A Tag hidden in only one of the two datasets (in practice a dataset's own defining Tag while Genre Tags are shown) is **set aside** for this pair: removed from both Clusters' Tag sets before any figure, flag or Tag-group count, and listed separately (below). Tags hidden or removed in both networks appear nowhere.
- **Only Multi-Tag Clusters are matched.** A **Cluster Match** is every pair (Cluster a of A, Cluster b of B), both Multi-Tag, sharing at least one Tag. One Cluster can have several.
- **Figures of a match**, with n = |a ∩ b|, sizes |a|, |b| (set-aside Tags excluded) and their Comparable parts a′ = a ∩ C, b′ = b ∩ C:
  - **Match Jaccard** = n / (|a| + |b| − n). Ranks the matches and takes the minimum. Tags not in the other network count against it.
  - **Shared, % of A** = n / |a| and **Shared, % of B** = n / |b|; their comparable forms n / |a′|, n / |b′| ("—" when that Cluster has fewer than two Comparable Tags).
  - **Jaccard (comparable)** = n / (|a′| + |b′| − n); "—" when either Cluster has fewer than two Comparable Tags. The match stays listed and ranked by Match Jaccard.
  - **Overlap vs. expected** = n / E with E = |a′| · |b′| / N, N = |C| (One-Tag Clusters included). Shown only in a match's detail, as a sentence; never a ranking or a sort column. No p-value or z-score.
  - The minimum of the two shares is not shown as a figure of its own.
- **Unshared Tags of each Cluster in a match** fall into four groups, labelled with the other dataset's name (B = Overall):
  - "in Overall C5" · *„в Overall C5“* (another Multi-Tag Cluster of B, named);
  - "One-Tag Cluster in Overall" · *„еднотагов клъстер в Overall“* (never "isolated");
  - "not in Overall's network (2 games, minimum 5)" · *„не е в мрежата на Overall (2 игри, минимум 5)“*, one group for "below g" and "in none of B's games" ("0 games");
  - "hidden in Strategy (its defining Tag)" · *„скрит в Strategy (определящият му таг)“* (set aside; in no figure).
- **Per-Cluster flags**, for each Multi-Tag Cluster of A against B (and the reverse), set-aside Tags ignored, one "No match:" family:
  - **"No match: outside Overall's network"** · *„Няма съвпадение: извън мрежата на Overall“*: none of its Tags is a Comparable Tag;
  - **"No match: only One-Tag Clusters in Overall"** · *„Няма съвпадение: само еднотагови клъстери в Overall“*: it has Comparable Tags, but each is a One-Tag Cluster in B; the tooltip gives the counts ("3 Tags in One-Tag Clusters of Overall, 2 not in its network");
  - **"No match above 0.10"** · *„Няма съвпадение над 0,10“* (the minimum currently set): it has matches, none at or above the minimum. A Cluster whose Tags are spread one each over several Clusters falls here.
- **The pair overview**, per dataset pair:
  - **ARI (comparable Tags)** on the Comparable Tags with an edge in at least one of the two networks (the `selection.link` set); "—" below two such Tags;
  - **Comparable Tags**: their count and their share of each network's Tags, both ways ("38 Comparable Tags: 76% of Overall's, 54% of Puzzle's");
  - **games in common**: the games in both Top-N Datasets after the shared Minimum Months Filter;
  - the number of Cluster Matches.
  No AMI, no mean best Jaccard, and no warning for a lopsided pair.
- **Minimum similarity:** a user control on Match Jaccard, labelled "Minimum Match Jaccard" · *„Минимален индекс на Jaccard на съвпадението“* (short "Minimum Jaccard" · *„Минимален Jaccard“*), from 0 up, **starting at 0.10**. It hides weaker matches and drives the third flag; it is a view choice.

### Games in both Clusters

Source: [What are "the games in both Clusters" of a match?](issues/05-games-in-both-clusters.md)

- A game is in **games in both Clusters** of a match (a in A, b in B) when it is in **both Top-N Datasets** after the shared Minimum Months Filter, has at least one Tag of **all of a** (as counted in A's network) and at least one Tag of **all of b** (as counted in B's). This is the Cluster Inspector's rule (`cluster_games` in `network/tables.py`); no minimum count or share is added.
- **Columns:** Rank in A · Rank in B · Name · Matched in A (x / |a|) · Matched in B (y / |b|) · Tags (the game's Tags from either Cluster, the shared Tags marked). No "of its tags" share.
- **Sort:** Matched in A + Matched in B descending, then Rank in A, then Rank in B (A = the left dataset as shown).
- **Count line** above the list: "Of **N** games in both datasets: **k** in both Clusters, **x** only in A, **y** only in B, **z** in neither." Only the first group is listed.
- **Length:** the first `GAMES_SHOWN` (10) rows, then "Show all N".
- **Empty list:** "These two datasets have no games in common, so no game can be in both Clusters." when N = 0; otherwise "None of the **N** games in both datasets is in both Clusters."

### Reading against seed and threshold dependence

Source: [How is a match read against seed and threshold dependence?](issues/07-seed-and-threshold-dependence.md)

- **A written caution plus figures each dataset already has.** No new figure per match, no reseeding floor, no Membership Stability beside a match, and low stability is never marked.
- **Each dataset row shows** "Seed-Noise Floor 0.52 · NA 0.81" · *„Праг на шума 0,52 · NA 0,81“*: the run's stored floor and the cell's Neighbour Agreement for a dataset on a cell; the floor from its own noise-seed runs and NA "—" for a hand-set or no-run dataset. Each label's tooltip gives the full term and its "In short" line.
- **The caution**, in the guide section, the metric reference chapter, the in-app help and `comparison.json`:

  > A Cluster Match says that two Clusters, each found at its dataset's settings, share Tags. It is not evidence that the Clusters are real or that the datasets share a genre structure. A match can appear, vanish or change its Match Jaccard with the seed, with g and s, and with the resolution. Read it against each dataset's Seed-Noise Floor and Neighbour Agreement.

  > *Съвпадението на клъстери показва, че два клъстера, всеки намерен при настройките на своя набор, имат общи тагове. То не доказва, че клъстерите са реални или че наборите имат обща жанрова структура. Съвпадение може да се появи, да изчезне или да промени индекса си на Jaccard при друго начално число, при други g и s и при друга резолюция. Четете го спрямо прага на шума от началното число и съгласието със съседите на всеки набор.*

### Comparison State

Source: [What fixes one comparison, and what does its export hold?](issues/09-comparison-identity-and-export.md)

- **The key:** the Build; the shared settings (Clustering Weight, algorithm, Minimum Months Filter, hidden Genre Tags, removed Tags); and for each included dataset, in the Build's dataset order, its source and values: **on a cell**, the Parameter Selection settings key, g, s and the Selected Resolution; **set by hand or no run**, g, s, γ and the main seed. Pick vs. selected cell is not in the key.
- **`comparison_id`** = the first 12 hex of the SHA-256 of the key's canonical JSON, made as `state_id` is. The view shows it in the header.
- **View choices, never in the key:** the minimum similarity, "show weaker", the chosen pair, which dataset is A (⇄), the chosen Cluster box and match.
- **Record only:** no "Open comparison". The export names, per dataset, its `state_id` (hand / no run) or its run's settings key and Threshold Pair, so any one dataset can be rebuilt.

### Compute and caching

Source: [Where does each dataset's Network State come from, and how long does a comparison take?](issues/12-compute-and-caching.md)

- **A dataset on a cell** reads only its stored Selected Partition from the Parameter Selection cache (network Tags, edged Tags, labels, Selected Resolution, Seed-Noise Floor, Neighbour Agreement). No Network State; the network is not rebuilt. Tag names and games come from the loaded dataset.
- **A dataset set by hand or with no run** gets a light function in `network/state.py`, built from `build_network`, `cluster_graph` and `noise_seeds`: the network, one clustering with the main seed, and the noise-seed runs for its Seed-Noise Floor (no null replicates, centres, silhouette or node metrics). A test checks that its partition and floor equal `compute_state`'s at the same settings. It also yields the `state_id` of those settings for the export.
- **In the request:** no background job, progress or cancel. Budget: about 0.4 s per dataset on a cell, 0.1 s per hand-set dataset; **under about 5 s cold for five datasets** on the full Build.
- **Two server-side LRU memos**, small like `STATE_TABLES`: (a) one resolved partition per dataset, keyed by the Build, the dataset, the shared settings and the dataset's source and values; (b) every pair's matches, flags, ARI, Comparable Tags and match games, keyed by `comparison_id`, each unordered pair stored once. Minimum, pair, match and A/B swap are derived from (b) with no recompute. The export reads (b) whole.
- **While computing:** the previous view dims under one loading overlay for the whole mode; Export is disabled until it returns. A shared-setting change re-resolves every dataset in that request; one dataset's change reuses the others' memo entries.
- **Cells are read when the mode resolves** (opening, a settings change, a dataset change). Nothing polls for a Parameter Selection run finishing.

### The Cluster Comparison mode

Source: [What does the Cluster Comparison mode look like?](issues/06-look-of-the-mode.md), variant B of the prototype.

#### Header

The shared settings as one row of controls, the `comparison_id`, and the **Export CSV** button (right).

#### Sidebar (left), top to bottom

- **Datasets:** a compact table, one row per Top-N Dataset of the Build: include checkbox, the dataset's name in its colour, g, s and γ edited in the row, and under the name the **source line** and "Seed-Noise Floor · NA". The source line, by Threshold Pair, never "cell":
  - `pick`: "★ Selected Partition at g 9 · s 7 (chosen pair)" · *„★ Избрано разбиване при g 9 · s 7 (избраната двойка)“*
  - `cell`: "Selected Partition at g 10 · s 6" · *„Избрано разбиване при g 10 · s 6“*
  - `hand`: "Set by hand: one Leiden run, main seed" · *„Зададено ръчно: едно изпълнение на Leiden, основно начално число“*
  - `no_run`: "No Automatic Parameter Selection run: network defaults, one Leiden run, main seed · Open Parameter Selection" (and, when the run vanished, that it is gone)
  
  The first two carry the tooltip "found among the partitions of 10 scan seeds; no seed of its own". No seed number is shown. Each row links to Parameter Selection (below). The mode has no grid of its own.
- **Dataset pairs:** every pair of included datasets, **ranked by ARI (comparable Tags)**, highest first. Each row: ARI with a small bar, the Comparable Tags count with the two shares, the games in common. Clicking a row chooses the pair. On first open the top pair is chosen.

#### Main column, top to bottom

- **The pair's title** with a ⇄ button that swaps which dataset is on the left (A). The default A is the earlier dataset in the Build's order.
- **Minimum Match Jaccard** slider (right, above the diagram), with a "show weaker" link that draws hidden matches dashed.
- **The link diagram:** A's Multi-Tag Clusters in a column on the left, B's on the right, under column headings naming each dataset. Each box: the label ("C3"), Tag count, its Tags (clipped to two lines), its flag as a coloured badge, and a left border in the dataset's colour. A curve per Cluster Match at or above the minimum; its width and strength follow Match Jaccard and its value is written on it. Clicking a box shows only its curves and dims the Clusters it doesn't match; clicking again shows all. Clicking a curve chooses the match.
- A line under the diagram: how many One-Tag Clusters each side has, and that they are not matched.
- **Match detail:** the two Clusters' names; Match Jaccard, Shared % of A, Shared % of B, Jaccard (comparable) with the Comparable Tag counts; the Overlap vs. expected sentence ("3 shared Tags: 2.4× the 1.25 expected from the Cluster sizes (N = 38 Comparable Tags)"); three Tag columns, **Shared**, **Only in Overall C3**, **Only in Puzzle C1**, each unshared Tag with its group; then **Games in both Clusters**.
- **Empty states:** fewer than two datasets included ("Include at least two datasets to compare"); a pair with no Cluster Match; no match chosen yet (the detail asks to click a curve).

#### Naming and colour

- A Cluster standing alone (detail, Tag columns, tooltips, flags) is always written with its dataset: **"Overall C3"**. Labels are `C1…` per partition (`label_clusters`), so the same label in two datasets means nothing.
- **Each dataset has its own colour**, on its name everywhere and on its Cluster boxes. The Workbench's Cluster colours do not carry over.

#### Narrow widths

The sidebar collapses above the diagram as the Workbench's pill bar does; the diagram keeps its two columns and scrolls vertically.

### Moving between modes

Source: [How does the user move between Cluster Comparison and the Workbench?](issues/13-moving-between-modes.md)

- **`MODES`** in `app/layout.py` gains `"comparison"`; `?mode=comparison` opens it. The mode is one more block of the one page (`arrange`).
- **No route between the comparison and the Workbench**, either way: no "Open in Workbench", and the Workbench's values are never sent in. Apply to Workbench stays in Parameter Selection.
- **The comparison's state survives every mode switch** (included datasets, sources and values, chosen pair and orientation, chosen match, minimum, "show weaker"). **On a Build switch** the mode stays open and starts fresh, every dataset on its pick.
- **The dataset row's link** opens Parameter Selection on that dataset (`ps-dataset`) with its current cell highlighted (`ps-pair`); for a hand-set or no-run dataset, on its pick or with no cell highlighted.
- **Parameter Selection gains "Use in Cluster Comparison"** · *Използвай в сравнението на клъстери* beside Apply to Workbench, always shown. It sets the highlighted cell as that dataset's values (source `cell`; the dataset is included if it was not), resolves and switches mode. Enabled under Apply to Workbench's rule (a cell with a Selected Partition), and **disabled when Parameter Selection's current settings differ from the comparison's shared settings** (including a shown defining Tag), with the tooltip "The Cluster Comparison uses other shared settings; this cell comes from a different run." · *Сравнението на клъстери използва други общи настройки; тази клетка е от друго изпълнение.* Help key `selection.use_in_comparison`: "Put this cell into the Cluster Comparison for this dataset and switch there. Available only when Parameter Selection's settings are the comparison's shared settings." · *Поставя тази клетка в сравнението на клъстери за този набор и превключва към него. Достъпно е само когато настройките на избора на параметри съвпадат с общите настройки на сравнението.*

### Export

Sources: tickets [09](issues/09-comparison-identity-and-export.md), [11](issues/11-names-and-readings.md) (column renames), [14](issues/14-defining-tag-in-a-match.md).

- **One "Export CSV" button** in the header, disabled while computing. It writes **`steamstudy_cluster-comparison_<comparison_id>_<UTC timestamp>.zip`** holding **every pair of included datasets**, whatever is on screen, A always the earlier dataset in the Build's order, and tables byte-identical for the same inputs.
- **Six CSVs**, a new group `cluster_comparison` in `src/steamstudy/export/schema.py` (bumps `SCHEMA_VERSION` from 6 to 7; every column gets its description, guide entry and panel per that file's conventions):
  - `datasets.csv`, one row per included dataset: `dataset`, `source` (`pick` / `cell` / `hand` / `no_run`), `g`, `s`, `resolution`, `seed` (empty on a cell), `selection_key` (cell only), `state_id` (hand / no run only), `n_games`, `n_tags`, `n_multi_tag_clusters`, `n_one_tag_clusters`, `hidden_tags`, `seed_noise_floor`, `neighbour_agreement` (empty off a cell).
  - `clusters.csv`, one row per dataset × Cluster, One-Tag Clusters included: `dataset`, `cluster`, `n_tags`, `tag_ids`, `tags` (each network's whole partition).
  - `pairs.csv`, one row per pair: `dataset_a`, `dataset_b`, `n_comparable_tags`, `comparable_share_a`, `comparable_share_b`, `ari_comparable`, `n_games_in_common`, `n_matches`.
  - `matches.csv`, one row per Cluster Match, every one regardless of the minimum: `dataset_a`, `cluster_a`, `dataset_b`, `cluster_b`, `n_tags_a`, `n_tags_b`, `n_shared`, `jaccard`, `share_a`, `share_b`, `comparable_jaccard` (empty below two Comparable Tags), `n_comparable_a`, `n_comparable_b`, `overlap_vs_expected`, `expected_overlap`, `shared_tags`, `only_a_tags`, `only_b_tags`, the unshared counts on each side split into in another Cluster / One-Tag Cluster / not in the network / hidden (defining Tag), and the game counts in both Clusters / only A / only B / neither.
  - `cluster_flags.csv`, one row per pair × direction × Multi-Tag Cluster: `n_matches`, `best_jaccard`, `flag`, with only the flags that do not depend on the minimum (`outside_network`, `only_one_tag_clusters`, or empty). A reader applies any minimum with `best_jaccard`.
  - `match_games.csv`, one row per match × game in both Clusters, unclipped: the match's keys, `appid`, `name`, `rank_a`, `rank_b`, `matched_a`, `matched_b`, `tags`.
- **`comparison.json`:** the full key and `comparison_id`, schema and software versions, Build provenance, the `columns` block generated from `schema.py`, the minimum on screen at export (information only), and the caution. No `.md` report.
- **Import Builds:** the files are declared as Steam files and `import_variant` derives the Import ones (`appid` → `id`, Steam-only columns per the rule). No Import-only file.
- **Help** for Export CSV:
  > Download every dataset pair of this comparison, whatever is on screen, as six CSV tables and `comparison.json` in one zip named with the `comparison_id`. Record only: it cannot be reopened. Disabled while a dataset is still being computed.

  > *Изтегли всички двойки набори на това сравнение, независимо какво е на екрана, като шест таблици CSV и `comparison.json` в един zip с `comparison_id` в името. Само за запис: не може да бъде отворен отново. Недостъпно, докато някой набор още се изчислява.*

### Modules

- **`steamstudy.network.comparison`** (new, Dash-free): resolved partitions in, every pair's Comparable Tags, set-aside Tags, Cluster Matches with their figures, Tag groups, flags, ARI and games in both Clusters out; the Comparison State key and `comparison_id`. The prototypes' `run.py` and `logic.js` are its reference.
- **`steamstudy.network.state`:** the light partition-plus-noise-seeds function.
- **`steamstudy.app.cc_view`** (new): the mode's layout, callbacks and the two memos; **`steamstudy.app.cc_export`** (new): the zip, after `ps_export`.
- **`steamstudy.app.ps_view`:** "Use in Cluster Comparison" and the row link's target. **`steamstudy.app.layout`:** `MODES`.
- **`steamstudy.export.schema`:** the `cluster_comparison` group.
- **Sentences** (readings, the caution, source lines, flags, empty states) live in one module, so the app, `comparison.json` and the guide test share one copy, as `selection_text` does for Parameter Selection.

### Readings

Each is the "In short" line of its metric-reference entry and so its tooltip; Bulgarian follows sentence by sentence in the catalogue.

- **Cluster Match:** two Multi-Tag Clusters, one from each dataset, that share at least one Tag; it says they share Tags, not that they are the same group.
- **Match Jaccard:** the shared Tags as a share of all Tags in either Cluster; 1 = the same Tags, 0 = none in common; a Tag missing from the other network counts against it.
- **Jaccard (comparable):** the same overlap on the Comparable Tags only; never lower than Match Jaccard, and the gap shows how much of a low score comes from Tags missing from the other network; "—" when either Cluster has fewer than two Comparable Tags.
- **Shared, % of A/B:** the share of one Cluster's Tags that the other also has; they differ when the sizes differ; 100% on one side means that Cluster lies wholly inside the other.
- **Overlap vs. expected:** shared Tags ÷ what two Clusters of these sizes would share if Tags were placed at random among the Comparable Tags; 1× = the sizes alone; descriptive, no p-value, since Clusters are not random draws.
- **ARI (comparable Tags):** how alike the two partitions are on the Comparable Tags with an edge in either network; 1 = identical, around 0 = no more than chance.
- **Comparable Tags (count and shares):** how many Tags are in both networks and what share of each network that is; a low share means the pair is compared on only a small part of that network.
- **Games in common:** the games ranked in both Top-N Datasets; shown, never scored.

No wording bands: each figure is read against its bounds and reference points (ARI 0 = chance; Overlap vs. expected 1× = the sizes alone); the full Build's ranges (ARI 0.07–0.53, Match Jaccard 0.03–0.58) appear only as "seen on the full Build" under "Compare with".

### Documentation and in-app help

Mirrored in `docs/user-guide/bg/`.

- **02 App controls:** `## Cluster Comparison mode` after Parameter Selection mode, opening with the caution as a callout. Subsections: Shared settings · Datasets (source line, Seed-Noise Floor, NA, include, editing g/s/γ, no route into the Workbench, pointing to Apply to Workbench) · Dataset pairs · Link diagram (⇄, clicking a box or a curve) · Minimum similarity and flags · Match detail · Games in both Clusters · Export CSV. Task recipe "Compare the Clusters of two datasets". Parameter Selection mode's section gains "Use in Cluster Comparison".
- **03 Metric reference:** chapter `## Cluster Comparison` after Parameter Selection, opening with "#### How a Cluster Comparison works" (holds the caution). Entries: Cluster Match and Comparable Tags · Match Jaccard and Jaccard on Comparable Tags · Shared share · Overlap vs. expected · ARI on Comparable Tags (links to the Adjusted Rand index entry) · Comparable Tags coverage · Games in common and games in both Clusters · No-match flags (including the hidden defining Tag group) · Comparison State and `comparison_id`. Usual In short / Bounds / Compare with / Exact definition blocks. Appendix B lists the new columns.
- **04 Files:** the zip, six CSVs and `comparison.json`.
- **05 Citing:** cite by `comparison_id`; record only, each dataset rebuilt from its `state_id` or its run's key and Threshold Pair.
- **06 Known limitations:** one Build only; a Threshold Pair's partition depends on the Parameter Selection cache.
- **In-app help:** every figure, label, flag badge, source state, the minimum slider, ⇄ and Export CSV get the tooltip of their entry (`help.py` reads each "In short" block).
- **bg:** every new string has a catalogue entry (parity test); `bg-terms.md` gains the five terms' rows.

### Resolved while writing this spec

These choices were implicit in the tickets and are made explicit here.

- **"Hidden Genre Tags" is a checklist**, as Parameter Selection's `ps-s-genre` is, not one on/off rule: the mode's control must match Parameter Selection's settings exactly for its runs to be found.
- **Set-aside Tags reach the flags too:** a Cluster whose only Comparable Tags would have been a defining Tag hidden on the other side is "No match: outside … network", not "only One-Tag Clusters".
- **On first open** every dataset is included and the top pair by ARI is chosen. When fewer than two datasets are included the pairs list and diagram show an empty state.
- **Export column names** beyond the tickets' (`dataset_a`, `cluster_a`, `n_tags_a`, `rank_a`, the flag codes `outside_network` / `only_one_tag_clusters`) follow `schema.py` conventions; final names at implementation.
- **`SCHEMA_VERSION`** goes from 6 to 7.
- **Module names** (`network/comparison.py`, `app/cc_view.py`, `app/cc_export.py`) follow the `ps_*` pattern.
- **Narrow widths** reuse the Workbench's pill bar, as Parameter Selection does.

## Out of scope

- **Similarity computed on games.** Two Top-N Datasets mostly hold different games, so game overlap would mostly measure how they were drawn. Games are shown for a match, never scored.
- **Multi-way matching** of one Cluster across three or more datasets at once.
- **The generated feature-analysis report.** Cluster Comparison is an app mode with its own export.
- **Comparing datasets of different Builds** ([Can datasets of different Builds be compared?](issues/08-cross-build-comparison.md)): Tag identity, "shared" settings and one Build per tab would each need their own design. Meanwhile, two tabs side by side.
- **Rejected along the way:** Dice, cosine, weighted Jaccard, NMI, VI, AMI, mean best Jaccard, the minimum containment as a figure, p-values and z-scores; a shared seed or per-cell reproducing seed; a seed control; a defining-Tag control; per-match reseeding floors or Membership Stability; "Open in Workbench" and sending Workbench values in; an "Open comparison" path; a `.md` report; a background job for computing; layout variants A (matrix and match table) and C (heatmap).

## Issues

Implementation tickets, numbered after the map's decision tickets (01–14):

- [15: Comparison core](issues/15-comparison-core.md) (no blockers)
- [16: Resolving each dataset's partition](issues/16-resolving-dataset-partitions.md) (no blockers)
- [17: User Guide, glossary, help keys and the sentences module](issues/17-guide-glossary-help-and-sentences.md) (15)
- [18: Mode: shared settings, dataset table and pair list](issues/18-mode-skeleton.md) (15, 16, 17)
- [19: Link diagram, Minimum Match Jaccard and flags](issues/19-link-diagram-and-minimum.md) (18)
- [20: Match detail and games in both Clusters](issues/20-match-detail-and-games.md) (19)
- [21: Editing datasets, shared-setting changes and state across switches](issues/21-editing-datasets-and-state.md) (18)
- [22: Routes to and from Parameter Selection](issues/22-routes-to-and-from-parameter-selection.md) (18)
- [23: Export CSV](issues/23-export.md) (18)
- [24: Full-Build acceptance check](issues/24-full-build-acceptance.md) (19–23)
