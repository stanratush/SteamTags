# Exclusion and genre-tag config contents
Type: grilling
Status: resolved
Assignee: ciberiyc@gmail.com
Blocked by: 04

## Question

What are the exact default contents of the config lists: sexual-content exclusion tags, software exclusion tags, Dating Sim, allowed app types; the default Genre Tag list for network hide/show; and whether store-genre values like Indie, Early Access, Free to Play are reported or omitted in the "most frequent genres" analysis? Also the exclusion-reason vocabulary recorded per game (first matching reason vs. all matching reasons).

Surfaced by Official Steam tag taxonomy extraction:
- Taxonomy reference: the official category table was removed from Steamworks (last Wayback copy 2026-05-08, unchanged since 2022); live `IStoreService/GetTagList` has 446 tags, 81 uncategorised. Which is the cited reference, and how are uncategorised tags handled?
- Sexual-content list: proposed `Sexual Content`, `Nudity`, `Hentai`, `NSFW` (if seen); undecided `Sexual Themes` (40500). Add a pre-freeze impact report (top-ranked games removed per excluded tag)?
- Software list: proposed `Software`, `Utilities`, `Animation & Modeling`, `Audio Production`, `Design & Illustration`, `Photo Editing`, `Video Production`, `Software Training`, `Benchmark`; undecided `Gaming`, `Desktop Companion`; keep `Game Development`.
- Default Genre Tag hide list: the 11 Top-Level Genres, optionally + `Indie`, `Massively Multiplayer`, `Early Access`, `Free to Play`.
- Matching: config keyed on `tagid` (or trimmed name); collector requests English; log every distinct tag string seen.

Surfaced by [Data source selection and substitution sign-off](07-data-source-signoff.md):
- The reason vocabulary must include `store_data_unavailable` (no store data and no Manual Metadata Entry) and `no_tags` (store page exists but shows no tags; from [Candidate pool definition](08-candidate-pool-definition.md)).
- Games added through a Manual Metadata Entry are checked against the same exclusion lists using their supplied tags.

## Answer

Resolved 2026-10-03 with the researcher. Evidence: [Official Steam tag taxonomy extraction](../research/04-steam-tag-taxonomy.md), [exclusion-tag impact check](../research/09-exclusion-tag-impact.md), [adult games and Dating Sim rank check](../research/09b-adult-games-and-dating-sim-rank.md).

**Matching and reference**
- Config lists are explicit `tagid` + name pairs; games are matched on `tagid` (the store page `InitAppTagModal` gives it). Names are labels only.
- Cited vocabulary: live `IStoreService/GetTagList`, snapshotted at collection time with its `version_hash`. The archived Steamworks table (Wayback 2026-05-08) is cited only as where list members were proposed from. Uncategorised tags need no handling: no rule depends on category.
- A configured tagid missing from the snapshot → warning, not failure. The collector logs every distinct `(tagid, name)` seen, with app counts.
- **Rank limit**: one global setting, default = anywhere in the displayed 20; any tag can be given its own, tighter limit. Dating Sim ships on the global default; it is tightened (if at all) only after the impact report. The "has tag" definition for datasets and the network is unaffected (always anywhere in the 20).

**Exclusion rules** (evaluated in this order; all matching reasons recorded with detail, `primary_reason` = first match; counts reported both overlapping and partitioned by primary reason). The first two short-circuit, since without store data nothing else can be evaluated.

| Reason code | Default config |
|---|---|
| `store_data_unavailable` | no store data and no Manual Metadata Entry |
| `app_type` | allowed types: `["game"]`; detail = actual type |
| `no_tags` | store page exists, no tags displayed |
| `adult_content` | Steam store page shows the "marked as 'Adult Only'" notice, **or** `appdetails.content_descriptors` contains id 3, **or** tag `Hentai` (9130) within its rank limit. Detail records which signal(s) fired. A Manual Metadata Entry must state adult-only status with a source. |
| `software_tag` | `Software` 8013, `Utilities` 87, `Animation & Modeling` 872, `Audio Production` 1027, `Design & Illustration` 84, `Photo Editing` 809, `Video Production` 784, `Software Training` 1445, `Benchmark` 5407; name-only entries `GameMaker`, `RPGMaker`, `Web Publishing` (apply only if seen). Not excluded: `Game Development`, `Programming`, `Coding`, `Gaming`. |
| `dating_sim_tag` | `Dating Sim` 9551 only; `Otome`, `Romance` are not exclusion grounds |
| `manual` | `manual_exclusion` list |

- Rule intent (glossary): adult content = games whose content is mainly sexual; mainstream games with nudity or sex scenes (Cyberpunk 2077, The Witcher 3, Baldur's Gate 3, GTA V) stay in. The `Sexual Content`, `Nudity` and `Sexual Themes` tags and store genre values are **not** exclusion grounds (no adult game sampled had a `Sexual Content`/`Nudity` genre).
- Dating Sim intent: games that are mainly dating sims. Known tension: at the shipped default, Stardew Valley (#17), Persona 5 Royal (#20), Persona 3 Reload and Monster Hunter Wilds (#11), The Sims 4 (#9) are excluded; real dating sims sampled all rank Dating Sim 1–5, but so do Fields of Mistria (#2) and Coral Island (#3). Resolved after the impact report via the per-tag limit and/or `exclusion_override`.
- **`manual_exclusion`** entries: AppID, name, written reason, ≥1 evidence URL with retrieval date, date added. Ships empty. First candidate to review: Banana (idle drop-farming app), after the impact report.
- **`exclusion_override`** entries: same shape plus the rule being overridden. Ships empty. Published.

**Content Flags** (config `content_flags`, matched anywhere in the 20, never filter; exported per game and counted in the feature analysis)
- `desktop_companion`: `Desktop Companion` 1320952 (always-on apps inflate concurrent counts; e.g. Bongo Cat).
- `sexual_content_tag`: `Sexual Content` 12095, `Nudity` 6650, `Sexual Themes` 40500, `NSFW` (name-only).
- Not flagged: `Idler`, `Clicker`.

**Genre Tag list** (network hide/show): the 11 Top-Level Genres `Action`, `Adventure`, `Casual`, `Experimental`, `Puzzle`, `Racing`, `RPG`, `Simulation`, `Sports`, `Strategy`, `Tabletop`; extendable by the researcher in config.

**Store genres in "most frequent genres"**: every observed value is reported with its numeric id; nothing is dropped. A config-assigned `kind` column (`genre` / `business` / `software`) marks values like `Indie`, `Early Access`, `Free To Play`, `Utilities`.

**Impact report** (generated before the lists are frozen; published with the datasets, extending the "would have scored inside a Top 100" report from [Candidate pool definition](08-candidate-pool-definition.md)):
- per rule and per matching tag/signal: games removed that would otherwise rank in each Top-100 Dataset, with would-be rank;
- near-misses: exclusion tags present beyond their rank limit;
- disagreements between the Adult Only notice and descriptor 3;
- Top-100 games carrying descriptor 1 or 4, a software store genre, or a Content Flag, that no rule excluded.
- After review, every config change is logged with a rationale; the config hash is stored in every export.

Glossary updated: **Exclusion** (rule intents, all reasons recorded, manual), new **Exclusion Override** and **Content Flag** ([CONTEXT.md](../../../CONTEXT.md)).
