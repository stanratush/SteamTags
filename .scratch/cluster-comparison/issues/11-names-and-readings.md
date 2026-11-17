# What are the measures called, and how is each one read?
Type: grilling
Status: resolved
Blocked by: 06, 07

## Question

[Which measures survive on the real Builds?](04-measures-on-real-builds.md) fixed what ships: whole-Cluster Jaccard (ranks; the minimum similarity applies to it, starting at 0.10), the two shared shares, Common-Tag Jaccard, Lift with the expected overlap in a match's detail, and ARI on the Common Tags with the Common Tags count and shares in the pair overview. [How do Tags missing from the other dataset's network enter a match?](02-tags-missing-from-the-other-network.md) left working names for the terms and flags.

Decide, in English and Bulgarian:
- the final name of each measure, term and flag (Cluster Match, Common Tags, the three groups of unshared Tags, "no overlap", "not in B's network", "no match above the minimum", the source line's four states), keeping clear of **Hennig's Jaccard**, **Whole-Cluster Jaccard**, **Lift** (of a Tag pair) and **Connection Ratio**;
- the one-sentence plain-language reading of each measure, and whether any gets wording bands (ARI and Jaccard ranged 0.07–0.53 and 0.03–0.58 on the prototype's data);
- which terms enter CONTEXT.md, and the outline of the User Guide section, the metric-reference entries and the in-app help entries.

Blocked by the look of the mode (which figures appear where) and by the seed and threshold reading (which caveats the wording must carry).

## Comments

- From [How is a match read against seed and threshold dependence?](07-seed-and-threshold-dependence.md): word the agreed caution (content in that ticket's answer, decision 5) in English and Bulgarian, and the "Neighbour Agreement" and "Seed-Noise Floor" labels in the dataset row.
- From [What fixes one comparison, and what does its export hold?](09-comparison-identity-and-export.md): name the comparison's identity (working name **Comparison State**, with a `comparison_id`), the `source` values (pick / cell / hand / no_run) as export codes beside their view wording, and the wording of the "Export CSV" help.

## Answer

Resolved with the researcher, 2026-11-17, in two rounds. Every new string needs its bg catalogue entry (ADR 0003); the Bulgarian below follows `docs/i18n/bg-terms.md`, whose table gains a row per new term with the implementation. Nothing enters CONTEXT.md until implementation.

**Facts that shaped the answer**

- In Bulgarian *общи* is already the word for "shared" (*минимум общи игри*), so "Common Tags" (in both networks) and "shared Tags" (in both Clusters) could not both use it.
- A One-Tag Cluster is "rarely a connected tag the algorithm left on its own" (CONTEXT.md), so "isolated" is not exact for it.
- The glossary reserves **Whole-Cluster Jaccard** (subsamples) and **Lift** (a Tag pair); the export column `lift` already means the latter in `associations.csv`.
- Parameter Selection's star is labelled "★ chosen" / *„★ избрана“* (`src/steamstudy/i18n/bg/ps_view.py`).
- In-app help is the tooltip made from each guide entry's "In short" block (`src/steamstudy/app/help.py`).

**Names** (English · Bulgarian)

1. **Cluster Comparison** (the mode) · *сравнение на клъстери*. **Cluster Match** · *съвпадение на клъстери* (pl. *съвпадения*); *съответствие* is avoided, as it suggests the Clusters really correspond. **dataset pair** · *двойка набори*, always qualified (*двойка* alone is the Threshold Pair). **Games in both Clusters** · *игри в двата клъстера*. **Comparison State** with its `comparison_id` · *състояние на сравнението*.
2. **Comparable Tags** · *сравними тагове* replaces the working name "Common Tags": the Tags in both networks, the only ones the comparison can judge a Cluster on. **shared Tags** · *общи тагове* is kept for the Tags two Clusters of a match have in common.
3. **Match Jaccard** · *индекс на Jaccard на съвпадението*, short label **Jaccard**: the headline figure (ranks; the minimum similarity applies to it). **Jaccard on Comparable Tags**, short label **Jaccard (comparable)** · *Jaccard (сравними)*, defined inside the Match Jaccard entry, not a term of its own.
4. **The shared shares get no term.** Shown as "62% of Overall C3's Tags are shared" · *„62% от таговете на Overall C3 са общи“*, the comparable form "71% of its Comparable Tags"; column headers **Shared, % of A** / **Shared, % of B**.
5. **Overlap vs. expected** · *припокриване спрямо очакваното* replaces the match "Lift", always as its sentence: "3 shared Tags: 2.4× the 1.25 expected from the Cluster sizes (N = 38 Comparable Tags)". **This amends the export of [What fixes one comparison, and what does its export hold?](09-comparison-identity-and-export.md):** `matches.csv` has `overlap_vs_expected` (not `lift`) beside `expected_overlap`, and `common_jaccard`, `n_common_a`, `n_common_b`, `n_common_tags`, `common_share_a/b`, `ari_common` become `comparable_jaccard`, `n_comparable_a`, `n_comparable_b`, `n_comparable_tags`, `comparable_share_a/b`, `ari_comparable`.
6. **ARI (comparable Tags)** · *ARI (сравними тагове)*, no new term; it links to the existing Adjusted Rand index entry.
7. **The three groups of unshared Tags**, under each "Only in …" column (B = Overall): "in Overall C5" · *„в Overall C5“*; "One-Tag Cluster in Overall" · *„еднотагов клъстер в Overall“* (never "isolated"); "not in Overall's network (2 games, minimum 5)" · *„не е в мрежата на Overall (2 игри, минимум 5)“*.
8. **The three flags, one "No match:" family:** "No match: outside Overall's network" · *„Няма съвпадение: извън мрежата на Overall“*; "No match: only One-Tag Clusters in Overall" · *„Няма съвпадение: само еднотагови клъстери в Overall“* (the counts in its tooltip); "No match above 0.10" · *„Няма съвпадение над 0,10“* (the minimum currently set). The working name "no overlap" is dropped.
9. **The source line**, by "Threshold Pair g · s", never "cell" (*клетка* is the heatmap's); export codes unchanged:
   - `pick`: "★ Selected Partition at g 9 · s 7 (chosen pair)" · *„★ Избрано разбиване при g 9 · s 7 (избраната двойка)“*
   - `cell`: "Selected Partition at g 10 · s 6" · *„Избрано разбиване при g 10 · s 6“*
   - `hand`: "Set by hand: one Leiden run, main seed" · *„Зададено ръчно: едно изпълнение на Leiden, основно начално число“*
   - `no_run`: "No Automatic Parameter Selection run: network defaults, one Leiden run, main seed · Open Parameter Selection"
   The first two carry the tooltip "found among the partitions of 10 scan seeds; no seed of its own".
10. **No wording bands** for any figure. Each is read against its bounds and reference points (ARI 0 = chance; Overlap vs. expected 1× = the sizes alone); the prototype's ranges (ARI 0.07–0.53, Match Jaccard 0.03–0.58) appear only as "seen on the full Build" under "Compare with".

**Readings** (each is the "In short" line of its entry, so the tooltip; Bulgarian follows sentence by sentence)

11. - **Cluster Match:** two Multi-Tag Clusters, one from each dataset, that share at least one Tag; it says they share Tags, not that they are the same group.
    - **Match Jaccard:** the shared Tags as a share of all Tags in either Cluster; 1 = the same Tags, 0 = none in common; a Tag missing from the other network counts against it.
    - **Jaccard (comparable):** the same overlap on the Comparable Tags only; never lower than Match Jaccard, and the gap shows how much of a low score comes from Tags missing from the other network; "—" when either Cluster has fewer than two Comparable Tags.
    - **Shared, % of A/B:** the share of one Cluster's Tags that the other also has; they differ when the sizes differ; 100% on one side means that Cluster lies wholly inside the other.
    - **Overlap vs. expected:** shared Tags ÷ what two Clusters of these sizes would share if Tags were placed at random among the Comparable Tags; 1× = the sizes alone; descriptive, no p-value, since Clusters are not random draws.
    - **ARI (comparable Tags):** how alike the two partitions are on the Comparable Tags with an edge in either network; 1 = identical, around 0 = no more than chance.
    - **Comparable Tags (count and shares):** how many Tags are in both networks and what share of each network that is; a low share means the pair is compared on only a small part of that network.
    - **Games in common:** the games ranked in both Top-N Datasets; shown, never scored.

**The caution** (content from [How is a match read against seed and threshold dependence?](07-seed-and-threshold-dependence.md))

12. > A Cluster Match says that two Clusters, each found at its dataset's settings, share Tags. It is not evidence that the Clusters are real or that the datasets share a genre structure. A match can appear, vanish or change its Match Jaccard with the seed, with g and s, and with the resolution. Read it against each dataset's Seed-Noise Floor and Neighbour Agreement.

    > *Съвпадението на клъстери показва, че два клъстера, всеки намерен при настройките на своя набор, имат общи тагове. То не доказва, че клъстерите са реални или че наборите имат обща жанрова структура. Съвпадение може да се появи, да изчезне или да промени индекса си на Jaccard при друго начално число, при други g и s и при друга резолюция. Четете го спрямо прага на шума от началното число и съгласието със съседите на всеки набор.*

13. **Dataset row labels:** "Seed-Noise Floor 0.52 · NA 0.81" · *„Праг на шума 0,52 · NA 0,81“*, each with a tooltip giving the full term and its "In short" line; NA is "—" off a Threshold Pair of a run. *Праг на шума* is a shortened form of the full term, accepted despite *праг* alone being avoided.

**Glossary and documentation**

14. **Five terms enter CONTEXT.md with the implementation**, each with its Avoid line: **Cluster Comparison** (avoid: cluster tracking, cross-dataset clustering); **Cluster Match** (avoid: correspondence, same cluster, shared cluster); **Comparable Tags** (avoid: common Tags, surviving Tags); **Match Jaccard** (avoid: Whole-Cluster Jaccard, similarity unqualified); **Comparison State** (avoid: comparison unqualified, session, view). Everything else lives in the metric reference only. `bg-terms.md` gains matching rows, with *съответствие* in Cluster Match's Avoid cell.
15. **Outline**, mirrored in `docs/user-guide/bg/`:
    - **02 App controls**: `## Cluster Comparison mode` after Parameter Selection mode, opening with the caution as a callout; subsections Shared settings · Datasets (source line, Seed-Noise Floor, NA, include, editing g/s/γ) · Dataset pairs · Link diagram (⇄, clicking a box or a curve) · Minimum similarity and flags · Match detail · Games in both Clusters · Export CSV; task recipe "Compare the Clusters of two datasets".
    - **03 Metric reference**: chapter `## Cluster Comparison` after Parameter Selection, opening with "#### How a Cluster Comparison works" (holds the caution); entries Cluster Match and Comparable Tags · Match Jaccard and Jaccard on Comparable Tags · Shared share · Overlap vs. expected · ARI on Comparable Tags · Comparable Tags coverage · Games in common and games in both Clusters · No-match flags · Comparison State and `comparison_id`; usual In short / Bounds / Compare with / Exact definition blocks. Appendix B lists the new columns.
    - **04 Files**: the zip, six CSVs and `comparison.json`.
    - **05 Citing**: cite by `comparison_id`; record only, each dataset rebuilt from its `state_id` or its run's key and Threshold Pair.
    - **06 Known limitations**: one Build only; a Threshold Pair's partition depends on the Parameter Selection cache.
16. **In-app help:** every figure, label, flag badge, source state, the minimum slider and ⇄ get the tooltip of their entry, as today. **Export CSV:**
    > Download every dataset pair of this comparison, whatever is on screen, as six CSV tables and `comparison.json` in one zip named with the `comparison_id`. Record only: it cannot be reopened. Disabled while a dataset is still being computed.

    > *Изтегли всички двойки набори на това сравнение, независимо какво е на екрана, като шест таблици CSV и `comparison.json` в един zip с `comparison_id` в името. Само за запис: не може да бъде отворен отново. Недостъпно, докато някой набор още се изчислява.*

**Follows from the above, not asked separately:** the minimum-similarity slider is labelled "Minimum Match Jaccard" · *„Минимален индекс на Jaccard на съвпадението“*, short "Minimum Jaccard" · *„Минимален Jaccard“*.
