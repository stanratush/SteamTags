# Eligibility constraints and selection defaults
Type: grilling
Status: open
Blocked by: 05

## Question

Which constraints make a Threshold Pair eligible, what are their documented defaults, and how exactly is the pair chosen?

- The constraints: minimum Information Retention, maximum share of isolated tags, minimum largest-connected-component share, a minimum and/or maximum number of Clusters, and "has a Selected Partition". Default values are justified by [Exploratory grid run on the current Build](05-exploratory-grid-run.md) and fixed before looking at which pair they select.
- From [Per-pair metric definitions](04-pair-metric-definitions.md): whether a pair needs a minimum number of comparable neighbours (with none, one lucky neighbour scores 1.0), and whether the share of identical-graph neighbours affects eligibility.
- The tolerance: within 0.05 of the maximum Neighbour Agreement among eligible pairs (configurable); then the smallest g, then the smallest s.
- What to report when no pair is eligible, and how the reasons for selection are worded for each dataset.
- Where the defaults live (`config/network.toml`? a new `[parameter_selection]` table?) and how they enter the cache key.
