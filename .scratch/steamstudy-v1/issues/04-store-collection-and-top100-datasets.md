# 04: Store collection and the five Top-100 Datasets

**What to build:** `steamstudy collect store` and `collect taglist` fetch store pages, `appdetails` and the `GetTagList` vocabulary for scored apps only. After that, `steamstudy build` writes all five Top-100 Datasets (Overall, Puzzle, RPG, Strategy, Simulation) to the app's loading contract. Exclusions are not applied yet, except that apps without store data cannot rank. This is the first point where the researcher can open a real ranked list.

**Blocked by:** 03

**Status:** done

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Collect" (sources, store politeness, stages 3–4), "Build" (Datasets and ranking, Build folder, `top100_<dataset>.csv`).

- [x] `collect store` fetches the store page and `appdetails` (`l=english`, no `cc=`) only for apps that `score()` scores, at the store rate over one shared connection. The age-check cookie uses a birth date 30 years before the collection date.
- [x] Store fetches end in the final outcomes `no_store_page` (redirect to home or to a page with no app), `age_gate` (flagged for review, no workaround) and `no_appdetails`. The store-reported country is recorded in `snapshot.json`.
- [x] `collect taglist` fetches `GetTagList` once when the store stage starts, with its `version_hash` recorded.
- [x] Pure parsers: `parse_store_page` gives the tags in display order (tag id, name, votes) and the Adult Only notice; `parse_appdetails` gives type, name, `is_free`, genres, release date and `content_descriptors`; `parse_tag_list` gives the vocabulary.
- [x] `datasets.toml` defines the five datasets. The defining tag ids are checked against the vocabulary snapshot, and "has tag" means anywhere in the displayed list.
- [x] Ranking runs over the Eligible Pool: `mean_monthly_players` desc, `months_observed` desc, `appid` asc. Always exactly 100 rows. `reports/ties.csv` lists the games tied with rank 100 that fell outside it.
- [x] `top100_<dataset>.csv` follows the spec's column contract exactly through a declared schema: 6-decimal score, `YYYY-MM` Release Month, matching `;`-lists. The Build fails if a name contains `;`.
- [x] `monthly_players.csv` (no Placeholder Rows), `tag_vocabulary.csv` and `release_month_check.csv` are written. `release_month_check.csv` uses a signed `months_apart` (positive = store date later), the `analysis.toml` threshold applied to |`months_apart`|, and an empty cell for an unparseable store date.
- [x] Apps with no store data or no tags do not rank (the rule is formalised in ticket 07).
- [x] Fixture tests include Baldur's Gate 3 1086940 (Early Access gap shows in `release_month_check.csv`), a free-to-play game (`is_free`), and a tie at rank 100.

## Comments

- 2026-10-04 (agent): Implemented with tickets 07 and 08 in one commit: store/taglist stages, store parsers, ranking with ties.csv, top100 contract, monthly_players (the scored months only), tag_vocabulary, release_month_check. A dataset with fewer than 100 eligible games (test Snapshot) is written short with a Build warning.
- 2026-10-05 (agent, audit): Audit: all criteria met. 'Always exactly 100 rows' was only a warning before; a full Build now fails when a dataset has fewer than 100 eligible games (researcher decision 2026-10-05). A test Build may be shorter, with a warning.
