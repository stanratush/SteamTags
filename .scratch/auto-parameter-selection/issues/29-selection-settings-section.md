# 29: Selection settings section

**What to build:** the Controls column's staged "Selection settings" section. The user edits hidden tags, removed tags, Minimum Months, the Clustering Weight and the minimum Multi-Tag Clusters, then switches the mode to that settings key with "Use these settings". The read-only settings are shown with their values. The Inspector's Remove action and "Copy from Workbench" feed the staged list.

**Blocked by:** 28

**Status:** ready-for-agent

Spec: [Automatic Parameter Selection spec](../spec.md): "Selection Settings" (editable and read-only), "Controls column" item 3, the settings label, "Labels".

- [ ] **Editable:**
  - the Genre Tag checklist and "hide each dataset's defining tag";
  - a removed-tags picker (all of the Build's tags) with the staged list;
  - the Minimum Months slider (0–60);
  - Clustering Weight (Lift | Shared games);
  - the minimum Multi-Tag Clusters (1–10).

  Each control has `selection.*` help, and Selection settings carries the weight / γ̂ sentence.
- [ ] **Read-only:** algorithm Leiden with its one-line reason, the Parameter Grid, the γ step, 10 scan seeds, R and S.
- [ ] Edits are staged. **Use these settings** switches the active `SelectionSettings`, and the mode then shows that key's cache (or "not run"). **Reset to defaults** restores the configured defaults. No edit starts a job. The active settings last for the session, and the app opens on the defaults.
- [ ] "Copy from Workbench" copies the Workbench's hidden tags, Minimum Months, Clustering Weight and removed tags into the staged edits, never g, s, γ or seed.
- [ ] The Pair Inspector's Remove action adds the tag to the staged removed list.
- [ ] A new minimum above an active constraint maximum raises the maximum to match, marked custom.
- [ ] The settings label sits below the section and in the explanation. The strip's "custom" marker and the loading panel's "Custom settings" reason use the same test.
- [ ] Tests:
  - Staging then Use switches the key (a different cache directory) and shows "not run".
  - Switching back shows the cached default results.
  - Copy from Workbench copies exactly the four kinds of setting.
  - Remove from the Inspector stages the tag.
  - Labels list each changed value next to its default.
  - A Run under custom settings removes the tag from every network (its absence is checked in the written graph files).
