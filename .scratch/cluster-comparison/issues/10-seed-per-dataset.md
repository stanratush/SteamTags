# Why does the seed change between cells, and should it be the same for every dataset?
Type: grilling
Status: resolved
Blocked by:

## Question

[Where do each dataset's g, s and resolution come from, and the shared settings?](03-per-dataset-defaults.md) takes each dataset's values from a cell of its Automatic Parameter Selection run "as Apply to Workbench does". That brings a seed with the cell: `workbench_setting` (`src/steamstudy/network/selection.py`) searches the two-decimal γ values inside the Selected Partition's Optimality Domain, nearest the midpoint first, and for each tries the main seed and then the scan seeds, keeping the first (γ, seed) at which Leiden reproduces the Selected Partition exactly. So the seed can differ from cell to cell, and so from dataset to dataset. The map was charted with the seed **shared**.

Explain and decide:
- why the seed changes: what the reproducing seed is for, how often it is not the main seed on the real Builds, and what a dataset's Clusters look like at the main seed when it is not;
- whether the comparison should use one seed for every dataset, and if so what it shows when that seed does not reproduce a cell's Selected Partition;
- the alternatives: the per-cell reproducing seed (as accepted provisionally); one shared seed with the cell's γ; or reading the cell's stored Selected Partition without re-clustering, so that no seed is involved for a cell;
- which seed a dataset "set by hand" or with no run uses, and whether the user can change a seed at all;
- how the choice is worded in the view, so that different seeds across datasets, if kept, do not read as an uncontrolled difference.

## Answer

Resolved with the researcher, 2026-11-17.

**Why the seed changes**

- A cell's Selected Partition is not the result of one seed. Automatic Parameter Selection runs Leiden with 10 scan seeds at every γ of the scan, pools the partitions, and CHAMP and the selection rule (both deterministic) choose one from the pool. Leiden is a randomised heuristic, so several seeds per γ give CHAMP a wider pool; the choice is then a property of the partition and the network, not of the run that found it.
- The scan seeds are derived from the main seed through their own stream (`derive_seeds`, stream 3; `selection_seeds` in `src/steamstudy/network/selection.py`). They are the same list for every dataset, Threshold Pair and γ, and the main seed is never one of them.
- The seed that "Apply to Workbench" carries is only an address: the Workbench shows what Leiden returns for one (γ, seed), so `workbench_setting` searches for a pair that returns the Selected Partition exactly, the main seed first. Which seed succeeds differs per cell.

**Measured on the stored runs** (Build 20261005T062558Z-full; Lift, Leiden, no Minimum Months Filter; cells with a Selected Partition)

| Dataset | Main seed | A scan seed | Not reproduced |
|---|---|---|---|
| Overall (latest run) | 97 | 29 | 3 |
| Overall (earlier run) | 112 | 41 | 0 |
| Strategy | 84 | 68 | 1 |
| Simulation | 81 | 49 | 1 |
| RPG | 56 | 71 | 3 |
| Puzzle | 62 | 68 | 1 |

- For cells that need a scan seed, the noise seeds agree with the Selected Partition at a mean ARI of about 0.77–0.88 and reproduce it exactly in about 20–40% of runs. The main seed itself was not run on those cells; the stored seed-noise figures stand in for it.
- For "not reproduced" cells the Workbench fallback has an ARI of 0.48–0.998 against the Selected Partition.
- So one shared seed would not make datasets more comparable: it would replace the validated Selected Partition with a different, seed-dependent partition in roughly 25–55% of cells.

**Decisions**

1. **A dataset on a cell shows the cell's stored Selected Partition.** The comparison reads it from the Automatic Parameter Selection run and does not re-cluster, so no seed is involved for a cell. This covers "not reproduced" cells too. It amends point 1 of [Where do each dataset's g, s and resolution come from, and the shared settings?](03-per-dataset-defaults.md): a cell gives g, s and the Selected Resolution, not a Workbench γ and seed.
2. **A dataset "set by hand" or with no run is clustered once with the Build's main seed**, the same for every such dataset. The mode has no seed control. (Points 4 and 5 of the defaults ticket stand as written.)
3. **The view shows no seed number for a cell.** The source line carries the explanation instead: a cell reads as the Selected Partition of the run (found with the 10 scan seeds); a hand-set or no-run dataset reads as one Leiden run with the main seed. Each dataset also shows its Seed-Noise Floor: the run's stored one for a cell, the Network State's own otherwise. The exact wording goes to the wording work.
4. **Opening a matched Cluster in the Workbench is not decided here.** The Workbench still needs a (γ, seed), so the reproducing seed and the "not reproduced" flag matter there; a note is added to "Moving between modes" on the map.

**Rejected**

- **The per-cell reproducing seed** (accepted provisionally before): it gives the same partition as reading the stored one where a seed reproduces it, fails for "not reproduced" cells, and shows differing seed numbers that read as an uncontrolled difference.
- **One shared seed at the cell's γ:** see the measurements above.
- **A one-seed scan in Automatic Parameter Selection:** it would make the main seed reproduce every cell, but only by shrinking CHAMP's pool tenfold; it redesigns Automatic Parameter Selection, invalidates every stored run, and is outside this map. Its effect on the Selected Partitions was not measured.
