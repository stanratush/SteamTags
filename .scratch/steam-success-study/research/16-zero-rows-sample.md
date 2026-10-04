# Steam Charts zero-row sample

Collected 2026-10-04 for [Placeholder rows and the Release Month definition](../issues/16-placeholder-rows-release-month.md). There were 39 plain GET requests in total. A subagent made 37 of them, 6 s apart, with curl and a descriptive User-Agent. Two more checked the newest month on app 730 and app 1086940. None returned a 403, 429, 503 or Cloudflare challenge. One returned HTTP 500 (app 1401150, Black Hole Simulator), so its no-rows state could not be re-confirmed. Every URL has the form `https://steamcharts.com/app/{appid}`.

## Checked

- 11 large or long-pre-release games: Scorn 698670, Hollow Knight: Silksong 1030300, Hades II 1145350, Manor Lords 1363080, Palworld 1623730, Enshrouded 1203620, Stardew Valley 413150, Baldur's Gate 3 1086940, Cyberpunk 2077 1091500, Kingdom Come: Deliverance II 1771300 and Ori and the Will of the Wisps 1057090.
- 20 low-player or dead apps taken from `/top/p.400` and `/top/p.460`.

## Findings

- **Leading 0.00/0 rows are rare.** Of the 11 large games, only Scorn has one: `September 2017 0.00/0`, then a 60-month gap, then `October 2022 1044.46/5387`. The other 10 start at their real launch or Early Access month with large values, e.g. Silksong `September 2025 191124.39/462134` and BG3 `October 2020 16792.37/48418`. No app had several leading zero rows, and none had a zero row right next to its first real month.
- **Interior 0.00/0 rows exist, but rarely.** Bold Blade 749110 has `May 2019 0.01/1`, `April 2019 0.00/0` and `March 2019 0.04/2`. Its other dead months are simply missing (gaps from Mar 2019 to Jan 2019, from Jan 2019 to Nov 2018, and others). So the site writes an explicit zero row only some of the time.
- **No trailing 0.00/0 rows were found.**
- **Gaps mean the app wasn't tracked, not that it had zero players.** Some apps' month rows stop while "Last 30 Days" still shows players. Bold Blade's rows end in May 2019, but its Last 30 Days is `0.00/1`. Hive 251210 jumps from January 2026 back to February 2024. 1701 A.D. 7870 jumps from Sep 2025 to Sep 2023, then to May 2021. Short internal gaps of 2–5 months are common among low-player apps.
- **Tiny nonzero rows before launch exist.** Stardew Valley has `December 2015 0.60/3` and `January 2016 0.53/3`, then `February 2016 1594.72/24496`, which is the real launch.
- **Smallest values seen in month rows:** `0.01/1` (Bold Blade May 2019, MY 1980's DASHBOARD 786630 July 2019, Black Dream 810470 March 2018). No month row had Avg 0.00 with Peak ≥ 1, and no row anywhere had Avg > 0 with Peak 0. Avg 0.00 with Peak ≥ 1 is common in the `Last 30 Days` row (e.g. 786630, 639870, 1004410 and 2888870). So rounding to 0.00 happens on the site, even though no month row showed it.
- **No other oddities:** no duplicate months and no in-progress current-month row. The only label that isn't a month is `Last 30 Days`. Rows always run strictly newest first.
- **Some apps have no month rows at all,** mostly DLC, soundtracks and dead games: 1259310, 1873040, 3131120, 2228690, 1405400, 4149060 and 3602500. Others have only `Last 30 Days`, e.g. Dadish 3D 2888870 and Cellchemist 4254360.
- **Names in the HTML are entity-encoded,** e.g. `Baldur&#39;s Gate 3`.

## Correction

The subagent reported that every page it fetched lacked a September 2026 row. A direct check on 2026-10-04 contradicts that: app 730 (Counter-Strike 2) and app 1086940 (Baldur's Gate 3) both list `September 2026` right after `Last 30 Days`. The research of 2026-10-02 agrees with the direct check. Low-player apps without a recent row are ordinary Missing Months. Their absence does not mean the site lags.
