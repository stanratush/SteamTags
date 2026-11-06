# Where does the analysis assume Steam?
Type: task
Status: resolved
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

## Answer

Findings: [Steam assumptions downstream of the Build](../research/01-steam-assumptions.md) (as of `65847aa`). 46 findings: 24 data, 13 config, 9 wording, 0 links out.

- **The seam already exists.** The network and the app read a dataset only through `BuildContext.rows()` → `games_from_rows()`: six columns (`appid`, `name`, `rank`, `months_observed`, `tag_ids`, `tags`). Beyond those, they need only two config facts: the defining tag and the Genre Tags.
- **Steam-only fields are read only by `analysis/`, which runs inside the Build stage.** That covers `is_free`, store genres, Content Flags and the Eligible Pool. The pool comes from in-memory store data, and only its size is written down. An import without these fields loses parts of the feature-analysis report, not the app.
- **No links out, and no `TOP_N` or 20-tag maximum downstream.** Those live in `collect/`, `build/` and `config.py`.
- **Import blockers:** the `builds/<snapshot_id>/<build_id>/` layout (Open Network State, the bundle), the eight required config files plus a Steam Charts stub, and the strict `TOP100` header check.
- **Eight places where generalising would change a Steam result.** The main ones: the `min_months` name inside every `state_id`, integer tag-id order feeding seeded clustering, rank order feeding the null model, the strict header, and `build.json` hash identity. All are avoided by adapting at read time and keeping Steam values verbatim.
