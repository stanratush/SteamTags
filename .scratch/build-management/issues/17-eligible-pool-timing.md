# How long does computing each dataset's Eligible Pool take on the lightweight Snapshot?
Type: task
Status: resolved
Blocked by:

## Question

The Build menu shows each dataset's Eligible Pool against its list size ([Build menu](12-build-menu.md)), but the prototype only estimates it. A whole Build takes about 24 s from the [lightweight Snapshot](08-lightweight-snapshot.md), and [Build inputs and timings](02-build-inputs-and-timings.md) measured the stages from the raw Snapshot.

Measure on the full Snapshot, with the script in `prototypes/17-eligible-pool-timing/` and findings in `research/17-eligible-pool-timing.md`:
- loading the lightweight tables once, then (warm) running every Exclusion Rule and computing the Eligible Pool and the Top-N for all datasets;
- how that time changes with one edit: a rule's tags, a rank limit, Tag Depth, one Manual Exclusion or Override, and a list size;
- whether an incremental path (reusing parsed tables or the matched rules) is materially faster than a full recompute;
- the same on the largest Import the warnings allow (50,000 items, 5,000 attributes), using synthetic data.

## Answer

Findings: [How long the Eligible Pool and Top-N take to recompute from a lightweight Snapshot](../research/17-eligible-pool-timing.md). Script and raw numbers: [prototypes/17-eligible-pool-timing/](../prototypes/17-eligible-pool-timing/).

- **Load once:** reading a stand-in lightweight Snapshot (6.06 MB zip) into the Build's records takes **2.8 s**; the largest Import (50,000 items, 5,000 attributes, 8.3 MB CSV) takes **2.4 s**. From the raw Snapshot the same records take 74–117 s.
- **Warm preview** (manual-list validation, Manual Metadata Entries, every Exclusion Rule, Content Flags, five datasets ranked, games entering Overall): **0.34 s on Steam, 1.3 s on the largest Import**. It matches the raw records exactly (every Eligible Pool, Top-100 and tie list).
- **One edit** (a rule's tags, a rank limit, Tag Depth, one Manual Exclusion or Override, list size) costs the same as a full preview: 0.28–0.36 s on Steam, 1.05–1.23 s on the Import.
- **Incremental** (reuse the unedited rule matches, re-run one rule or one game, then rerank) gives 0.13–0.15 s on Steam, **not material**, and 0.40–0.67 s on the Import. A list size edit is a re-slice (< 1 ms). Ranking costs as much as the rules (0.13 s against 0.14 s on Steam), because the scope test scans each game's tags; every path still pays for it.
- **Not covered:** the feature analysis, network stage and reports (about 20 s of a Build), the app process and job overhead, and memory. The lightweight Snapshot and named rules are stand-ins until implemented.
