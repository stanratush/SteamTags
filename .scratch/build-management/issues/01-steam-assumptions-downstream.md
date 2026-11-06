# Where does the analysis assume Steam?
Type: task
Status: open
Blocked by:

## Question

List every Steam-specific assumption **downstream of the Build**, so that [What is the generic dataset contract?](04-generic-dataset-contract.md) can draw the seam. Done AFK. Findings go in `research/01-steam-assumptions.md`.

For each module in `network/`, `analysis/`, `app/`, `export/`, `i18n/` and `bundle/`, record what it reads that only Steam has:
- field names (`appid`, `months_observed`, `mean_monthly_players`, `tag_ids`, `is_free`, `genres` …);
- file names (`top100_<key>.csv`, `monthly_players.csv`, `build.json` keys);
- config facts (defining tag, Genre Tags, `genre_kind`, `hide_defining_tag`, the 20-tag maximum, `TOP_N = 100`);
- wording (Steam, Steam Charts, game, tag) in UI strings, report templates and export headers;
- links out (store URLs, Steam Charts URLs).

Mark each one as **data** (needs a generic field), **config** (needs a generic setting) or **wording** (kept under the Steam-tool decision). Count them per module. Note anything that would change a Steam result if it were generalised.
