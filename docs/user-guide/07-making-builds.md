# Making Builds in the app

This chapter is for researchers who make Builds: from the repository (`uv run steamstudy app`, see the [Running Guide](../running-guide.md#the-app)), or from an App Bundle made **with its sources** (it carries each Build's lightweight Snapshot or Import and the default settings; its `READ ME FIRST.txt` says so). An App Bundle of Builds only opens the Builds it carries: there, only [See a Build's settings](#see-a-builds-settings) applies. A Build never changes once it is made: to try other settings you make a new Build from a **draft**, a set of settings that is saved as you edit it and becomes a Build when you build it. Settings that need interpreting link to their entries in [chapter 3](03-metric-reference.md); this chapter says only where to find them and what each step does.

## The Build tree

Click the Build's name in the header to open the Build menu. It shows one tree per Snapshot and per Import, with the forms the Snapshot has (raw, lightweight) beside its id. Each tree's heading has a **+ New Build** button, which starts a draft from the defaults: `config/` for a Snapshot (the defaults in the repository's `config/` folder) or the Import defaults for an Import.

Under the heading are the Builds, each under the Build it was made from. A Build row shows its name, chips (**✓ open in this tab**, **latest**, **test**), its date and a short summary of its Top-N (for example "Overall 100 · Puzzle 100"). A Build whose parent was deleted sits at the top level and reads "from a deleted Build"; a Build duplicated from another Snapshot's Build sits at the top level of its own tree and names that Build and Snapshot.

Draft rows sit under the Build they started from (or at the top of the tree, when they started from the defaults) and show their state: **draft**, **running %** while a Build run is working on them, or **failed** after a failed run. They also show how many settings differ from where the draft started, and when it was last saved.

Click a Build to switch this tab to it ([Switch Builds](01-getting-started.md#switch-builds)). Press **+ New Build** to start a draft from the defaults, and click a draft row to open it. Click outside the menu or press Esc to close it.

## Start a draft

There are three ways to start one:

- **From the defaults:** press **+ New Build** in the tree's heading. The draft starts from `config/` (or the Import defaults) and has no parent.
- **Duplicate:** press **Duplicate** on a Build's row, or press **Duplicate the open Build** below the tree. The app asks which Snapshot the new Build should read; the default is the parent's own. A Build of an Import can only be duplicated within that Import.
- **Discard:** press **Discard** on a draft's row to delete it.

A draft is saved after every edit; **Close** keeps it, and it reopens from the tree. A draft whose settings equal an existing Build's may still be built: Review names that Build and says that building again is allowed.

## The steps of a draft

The draft dialog has six steps, listed on its left. A step's marker turns **green** when it holds changes from the parent (or the defaults) and **red** when something in it must be fixed before Build. Each step's `?` opens its section here.

### Start {#draft-start}

Name the Build and say why it exists:

- **Name:** unique among the Builds and drafts of the same Snapshot or Import, ignoring case. Readers see it beside the `build_id` in the app, in bundles and in citations.
- **Description:** required; it becomes the Build's changelog entry.

The step also shows what the draft started from and which Snapshot or Import it reads. If the last Build run of this draft failed, the step shows why: the number of pages that did not parse with the path of the CSV that lists them, or the causal word found in a report with its sentence.

A Snapshot with only its raw form shows **Make lightweight Snapshot**. It makes the lightweight form as a background job (about 80 s), after which the Eligible Pool preview works and a Build takes about 24 s instead of about 99 s ([Raw and lightweight Snapshots](#raw-and-lightweight-snapshots)).

### Changes the Top-N {#draft-top-n}

The settings that decide which games are in each Top-N Dataset:

- **Datasets:** add, remove and relabel datasets, and give each a defining tag and a [List Size](03-metric-reference.md#list-size). The defining tag is picked from the source's own tags: the Snapshot's Steam tag list, or an Import's attributes. `overall` cannot be removed or given a defining tag. Each row shows the dataset's Eligible Pool, as previewed for the current settings.
- **[Tags per game (Tag Depth)](03-metric-reference.md#tags-per-game-tag-depth):** a number, or **all**.
- **Global rank limit** and, for Steam only, the allowed app types.
- **Exclusion rules:** the named rules, one card each, between the fixed rules that always run first and last (shown, not editable). A card holds the rule's name, and its label and signals (tags with optional rank limits, name-only matches) as text. **↑** and **↓** change the order, which decides each excluded game's primary reason; **Add a rule** adds one. Renaming a rule also renames its Exclusion Overrides. **×** deletes a rule; when the rule has Exclusion Overrides, the dialog asks first and deletes them with it. See [Exclusions and would-be ranks](03-metric-reference.md#exclusions-and-would-be-ranks).

Hover over a setting's dotted label for its short explanation, and click it for the full entry.

### Curation {#draft-curation}

The researcher-maintained lists: Manual Exclusions, Exclusion Overrides and (Steam only) Manual Metadata Entries. Each entry needs a reason and evidence and is checked as the Build checks it. The excluded games that would rank in Overall are listed on Review, each with **Keep it**: it adds an Exclusion Override for each rule that excludes the game and opens this step, where you fill in the reason and evidence.

### Reports and analysis {#draft-reports}

The Content Flags (the `[[content_flag]]` part of `exclusions.toml`: they mark games for the reports and never exclude one), the Genre Tags and the feature-analysis settings (`analysis.toml`: `max_itemset_size`, `min_support`, the causal words, the release-month check for Steam). A causal word that appears in a generated report fails the Build run.

### Network defaults {#draft-network-defaults}

Every `network.toml` key, including the Parameter Grid and the Pair Constraints. Under it the step lists warnings per dataset, naming the dataset and its N: the grid's largest g above N, a default g or s above N, or `min_support` above N. These are warnings only; the draft can still be built. A grid with no pairs (its smallest s above its largest g) marks the step red and keeps Build off.

### Review {#draft-review}

Review is where Build is pressed. It lists:

- the **changed settings**, with the old value struck through and a Top-N badge on each change that alters which games are in a dataset;
- **identical settings** to an existing Build, if any;
- the **Eligible Pools**: each dataset's pool against its List Size, the games that would enter and leave Overall compared with the parent Build (or the latest Build of the source), and the excluded games that would rank in Overall;
- the **problems to fix**, each with a button that goes to its step.

The Eligible Pool numbers are a preview: they run the Build's own exclusion and ranking code on the source's records, so they equal what the Build will produce. The first time a draft of a source opens, the dialog reads that source's records ("Loading Snapshot…", a few seconds). **Build stays off until the preview matches the current settings.** After any edit the old numbers stay, dimmed, until the new ones arrive. A pool smaller than its List Size is a problem in a full Snapshot (a test Snapshot only warns). When a setting cannot be computed (an invalid rule, an override of an unknown rule), each number reads "—", with the reason and a button to the step that fixes it.

**Not previewed** means the Snapshot has no lightweight form, so its records are not loaded. Review says so, and Build stays on: the Build checks each List Size itself, from the raw pages, in about 99 s.

## A running Build

Pressing Build starts a Build run in a process of its own, shown in a strip under the header in every tab and every mode: the stage, the seconds against the estimate (about 24 s from a lightweight Snapshot, about 99 s from raw) and a bar. Only one Build runs at a time in the app; a second waits for the first. Switching Builds or closing the tab does not stop it; **Cancel** does, between stages.

When it finishes, the strip offers **Open it in this tab**: the app never switches by itself. The new Build appears in the tree, and the draft is gone. When it fails, the strip offers **Open the draft**: the draft keeps its settings, and its Start step shows the failure.

## See a Build's settings

Every Build row in the Build menu has **Settings…**, in App Bundles too. It shows the Build's name, id, description and the Snapshot (and its form) or Import it was built from, then its settings by the draft's steps:

- **Changes the Top-N:** each dataset's defining tag, List Size and Eligible Pool, the tags per game, the exclusion limit (`global_rank_limit`: a rule's tag counts only within that many of a game's first tags), the app types (Steam), and each named exclusion rule with its signals. A rule's tag reads, for example, "Hentai (within the first 15 tags)": its own rank limit, or the exclusion limit.
- **Curation**, **Reports and analysis** and **Network defaults:** each settings file as the text a draft edits, folded until you open it.

Tags per game and the exclusion limit are separate settings. Exclusion reads a game's full tag list and comes first; tags per game decides afterwards which genre a remaining game belongs to and which tags form the network. A Build with 10 tags per game and the exclusion limit 20 still excludes a game whose Hentai tag is its 20th; set the exclusion limit to 10 too, on the Top-N step, for exclusion to look at the same 10 tags.

A Build never changes: to try other settings, Duplicate it into a draft.

## Manage and delete Builds {#manage-builds}

**Show sizes** below the tree adds each Build's folder size and app-cache size to its row; **Hide sizes** removes them.

**Delete** (on a Build's row) asks first and shows what it will do:

- which bundles named the Build;
- that exports made from it will no longer open with **Open Network State…**;
- where `latest` moves;
- which Builds and drafts lose their parent and move to the top level.

It cannot be undone. The Build open in this tab cannot be deleted: switch to another Build first. Removal Sensitivity and Parameter Selection runs that other tabs have going on the Build are stopped before it is deleted.

## Raw and lightweight Snapshots

A Snapshot has two forms with one id: **raw** (the folder of collected pages) and **lightweight** (one zip of the parsed tables, about 6 MB). A Build reads the lightweight form when there is one. Both forms give the same numbers: the only difference in a Build is `snapshot_form` in its `build.json`. The tree shows the forms each Snapshot has. A Snapshot with only its raw form can still be built (in about 99 s), but its drafts are not previewed. Make the lightweight form from the Start step, or with `steamstudy snapshot lighten` ([Running Guide](../running-guide.md#lightweight-snapshots)).
