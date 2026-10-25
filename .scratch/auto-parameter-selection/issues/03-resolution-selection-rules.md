# Resolution-selection rules
Type: grilling
Status: open
Blocked by: 01

## Question

Exactly how does one **Threshold Pair** get its **Selected Partition** and **Selected Resolution**, including every edge case?

- The γ scan: 80 values evenly spaced from 0.25 to 3.0 (linear or log?), 10 seeds per γ; or bisection, if [Resolution-selection formulas](01-resolution-selection-formulas.md) recommends it.
- Deduplicating partitions: equality as set partitions over all nodes, isolated tags included.
- The CHAMP range: is the envelope taken over [0.25, 3.0] only or over [0, 3.0]? How is a domain cut off at a range end treated (its width, its midpoint, its eligibility)?
- Self-consistent γ: evaluated once or iterated; what happens when it is undefined (ω_in ≤ ω_out, ω_out = 0, fewer than two groups), or when it falls outside the scan range.
- "At least three Multi-Tag Clusters": how One-Tag Clusters and isolated tags count.
- Ties on domain width; and the outcome when no Stable Partition qualifies (does the pair become ineligible with a recorded reason?).
- Rounding: `Settings` stores γ to 2 decimals (`resolution_text`). What if the domain is narrower than 0.01, or the rounded midpoint falls outside it?
- Recorded per pair: every Admissible Partition with its domain, γ estimate and stability flag, so the UI can draw the CHAMP plot.
