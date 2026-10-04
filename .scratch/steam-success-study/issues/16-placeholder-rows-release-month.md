# Placeholder rows and the Release Month definition
Type: grilling
Status: resolved
Assignee: ciberiyc@gmail.com
Blocked by: none

## Question

Steam Charts sometimes shows a 0.00 Avg. / 0 Peak row years before a game's real release (e.g. Scorn: Sep 2017, then nothing until Oct 2022). Under the current glossary, that row would become the Release Month and, if inside the Observation Window, be averaged as a real zero. How should placeholder rows be detected and treated (ignore rows with 0.00 avg and 0 peak? only leading ones? ones followed by a gap of N months?), and does the Release Month definition change accordingly? Also confirm that the rolling "Last 30 Days" row is never treated as a month, and how apps with no monthly rows at all are recorded (excluded with a reason vs. kept with `months_observed = 0`).

Context: [Steam Charts compliant access and coverage](01-steam-charts-access.md).

## Answer

Resolved 2026-10-04 with the researcher. Evidence: [Steam Charts zero-row sample](../research/16-zero-rows-sample.md). In that sample a 0.00/0 row was rare: one leading (Scorn), one interior (Bold Blade), none trailing. Dead months are usually omitted rows rather than zeros.

**Placeholder Row**
- A Steam Charts month row with Avg. Players `0.00` **and** Peak Players `0`, **wherever it sits** (leading, interior or trailing). It is not data. It is treated exactly like an omitted row.
- A row with Avg. `0.00` and Peak ≥ 1 is real data (someone played; the average only rounds to 0.00).
- No other thresholds. Any other value Steam Charts recorded stays a value. That includes tiny nonzero months before launch (Stardew Valley: `Dec 2015 0.60/3`), which count toward the score and `months_observed` if they fall inside the Observation Window.

**Release Month** = the first month with a Steam Charts row that is not a Placeholder Row. A Placeholder Row never counts toward `months_observed` and never enters the mean. The rule lives inside `score()` (see [Pipeline architecture and export schema](15-pipeline-architecture.md)).

**Row parsing**
- Only rows labelled `<English month name> <YYYY>` are months. `Last 30 Days` is always skipped without comment.
- Month rows newer than the Observation Window's last month are ignored, as the Observation Window definition already says. That is not an error.
- Unknown labels and duplicate months go to `reports/parse_errors.csv`, so the Build fails under the existing rule.

**Unscored apps** (still not an Exclusion; see [Candidate pool definition](08-candidate-pool-definition.md)): `completeness.csv` splits the unscored count three ways:
- no month rows;
- only Placeholder Rows;
- month rows, but none in the Observation Window.

**New Build reports** (in `reports/`)
- `placeholder_rows.csv`: `appid, month, position` (`leading` / `interior` / `trailing`) for every Placeholder Row in the Candidate Pool, with the count added to `completeness.csv`. Placeholder Rows never appear in `monthly_players.csv`. The `top100_<dataset>.csv` contract is unchanged.
- `release_month_check.csv`: a diagnostic only, never a rule. It lists Top-100 members whose Release Month differs from the store release date by more than a configurable number of months (default 3), with `appid, release_month, store_release_date, months_apart`. A store date that can't be parsed (e.g. "Coming soon") leaves `months_apart` empty. It is expected to be noisy for Early Access games, because the store shows the 1.0 date (Baldur's Gate 3: EA Oct 2020, store Aug 2023). It also catches tiny pre-launch rows like Stardew Valley's.

**Test Snapshot edge cases** to add to the list in [Pipeline architecture and export schema](15-pipeline-architecture.md):
- interior Placeholder Row: Bold Blade 749110;
- tiny pre-launch rows: Stardew Valley 413150;
- Early Access gap between dates: Baldur's Gate 3 1086940;
- only `Last 30 Days`: Dadish 3D 2888870.

**Known limitations** (for the spec):
- tiny pre-launch rows are kept as real data;
- Steam Charts pauses tracking of low-player apps, so gaps mean the app wasn't tracked, not that it had zero players;
- the release-date diagnostic is noisy for Early Access games.
