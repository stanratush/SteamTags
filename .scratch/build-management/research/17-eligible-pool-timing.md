# How long the Eligible Pool and Top-N take to recompute from a lightweight Snapshot

Facts for [When does the Build menu show each dataset's Eligible Pool?](../issues/18-eligible-pool-preview.md). As of commit `c755e30` (2026-11-07), Snapshot `20261005T062558Z-full`, the current `config/`. Windows 11, Python 3.14, one process, warm file cache.

How this was found: [measure.py](../prototypes/17-eligible-pool-timing/measure.py), in three modes. `extract` reads the raw Snapshot with the Build's own stage functions and writes a **stand-in lightweight Snapshot**: a zip of gzipped CSV tables with the fields the pool needs (6.06 MB, against 6.3 MB estimated in [Build inputs and timings](02-build-inputs.md)). The lightweight Snapshot is not implemented yet, so this is the closest shape. `steam` loads the zip into the Build's own records (`Score`, `Game`) and times a **preview**: the Build's validation of the manual lists, Manual Metadata Entries, `evaluate` (every Exclusion Rule), Content Flags, the five datasets ranked, and the games entering and leaving Overall. Each time is the median of 7 runs. `import` does the same on a synthetic Import. Raw numbers: [Steam](../prototypes/17-eligible-pool-timing/steam_20261005T062558Z-full.json), [synthetic Import](../prototypes/17-eligible-pool-timing/import_synthetic.json). The zip and the CSV were written outside the repository and deleted.

**Check:** the pools, the excluded set and every Eligible Pool, Top-100 and tie list computed from the zip are identical to those from the raw records (one SHA-256 over all lists).

## Short answer

- **Loading once costs about 2.8 s** (Steam, 10,973 scored apps) and **2.4 s** (Import, 50,000 items). That is paid once per draft (or per Snapshot) and kept in memory.
- **A full warm preview takes 0.34 s on Steam and 1.3 s on the largest Import.** Every edit measured costs about the same, because each one is a full recompute: 0.28–0.36 s on Steam, 1.05–1.23 s on the Import.
- **Incremental paths save at most about 0.2 s on Steam** (0.13–0.15 s against 0.34 s), so they are **not material there**. On the Import they cut 1.2 s to 0.40–0.67 s. A list size edit alone needs only a re-slice (under 1 ms).
- **Ranking is as costly as the rules.** On Steam, evaluating every rule takes 0.14 s, Content Flags 0.06 s, and ranking the five datasets 0.13 s. The ranking cost is the scope test (a scan of each game's tag list per dataset), not the sort. So every incremental path still pays for a rerank.
- **From the raw Snapshot the same records take 117 s to read** in this run (74 s in [Build inputs and timings](02-build-inputs.md), on a quieter machine). A preview without the lightweight Snapshot needs that read first.

## Steam (full Snapshot)

| Step | Seconds |
|---|---|
| Read the stand-in lightweight zip into `Score` and `Game` records (once) | 2.80 (2.63–2.88) |
| Full preview, unedited draft | 0.34 |
| — evaluate every Exclusion Rule | 0.14 |
| — Content Flags | 0.06 |
| — rank five datasets (Eligible Pool, Top-100, ties) | 0.13 |

One edit, then a full recompute, and the incremental path reusing the unedited draft's rule matches:

| Edit | Full | Incremental | Overall pool after | Entering Overall |
|---|---|---|---|---|
| Add one tag to a rule (`software_tags`; a common tag, deliberately extreme) | 0.28 | 0.13 (that rule only, then rerank) | 2,287 | 67 |
| Lower the global rank limit by 5 (on top of that) | 0.30 | — | 3,939 | 47 |
| Tag Depth 10 | 0.34 | 0.15 (rerank only) | 8,776 (Puzzle 1,245 → 924) | 0 |
| One Manual Exclusion (Overall's #1) | 0.34 | 0.15 (one game, then rerank) | 8,775 | 1 |
| One Exclusion Override | 0.34 | — | 2,287 | 67 |
| List size 500 | 0.36 | < 0.001 (re-slice) | 8,776 | 400 |

The edit does not change the time much: the work is a pass over every scored game either way.

## Synthetic Import at the warning limits

50,000 items, 5,000 attributes, 5–30 attributes per item drawn Zipf-like (15.3 on average, since repeats collapse), a log-normal score and one numeric filter field. The CSV is 8.3 MB. The settings are Import-shaped: three attribute rules, no Content Flags, Overall plus four defining attributes from common to rare.

| Step | Seconds |
|---|---|
| Read the Import CSV into records (once) | 2.42 (2.07–2.93) |
| Full preview, unedited | 1.30 |
| — evaluate every rule | 0.54 |
| — rank five datasets | 0.65 |
| Each single edit, full recompute | 1.05–1.23 |
| Incremental: one rule, then rerank | 0.40 |
| Incremental: one Manual Exclusion, or Tag Depth (rerank only) | 0.65–0.67 |
| Incremental: list size | < 0.001 |

The Overall pool is 47,674 items, so the sort and scope scan are about five times Steam's.

## What this does not cover

- **Not a Build.** The preview stops at the Top-N lists. It leaves out the feature analysis (8 s on Steam), the network stage (11.6 s) and the reports, and the Build's own name checks and vocabulary warnings (cheap: one pass over the Top-N and the configured ids).
- **Not the app.** It is one Python process with nothing else running. In the app the same work would share the process with Dash callbacks, or run as a job: the job's start-up and the transfer of results are not measured. Memory was not measured.
- **The lightweight Snapshot is a stand-in.** Its loader here is about 60 lines; the real one (ticket [What is a lightweight Snapshot?](../issues/08-lightweight-snapshot.md)) keeps more tables (listing rows, request-log outcomes) that the pool does not need. Loading those would add a little to the 2.8 s, not to the preview.
- **The rule edits use today's three tag rules**, not the generic named rules of [How do named exclusion rules work?](../issues/06-named-exclusion-rules.md). The per-rule work is the same tag scan, so the times should carry over; each extra rule should add about 0.03 s on Steam (estimated from 0.14 s for today's rules, not run).
- **Speed-ups not tried:** a per-game tag-id set cached once per draft would cut the scope test. The rerank cost is mostly that test.
