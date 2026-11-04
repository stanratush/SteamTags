# 19: The Inspector's Validation section

**What to build:** the Pair Inspector's Validation section at its bottom holds the **Validate this pair** button (moved from under Apply), the three-state null badge with its weak "⚠", the badge "Dissolved in most subsamples (re-selected): n", two R/A status strips with one square per Multi-Tag Cluster, the median ARI line, and a link to the card when the inspected pair is the card's pair.

**Blocked by:** 18

**Status:** done

Spec: [Validation review spec](../spec.md): "The Inspector's Validation section", "Resolved while writing this spec" (the static button). Verbatim strings: [bg-strings.md](../prototypes/11-bg-wording/bg-strings.md) ("Inspector's Validation section"; the run-time hint does not ship). Reference: [PROTOTYPE-validation-layout.html](../prototypes/06-validation-layout/PROTOTYPE-validation-layout.html). Source: [How should the validation card and the Inspector's Validation section look?](06-validation-card-and-inspector-layout.md).

- [x] **Placement:** in `ps_view.mode_layout`, a static container after `ps-inspector-body` holds the section, with the `ps-validate` button inside it; the button is removed from under Apply. The callbacks that toggle `ps-validate`'s style and `disabled` keep working. `inspector()` no longer renders the Validation H5.
- [x] **Header:** H5 "Validation" with its ? link.
- [x] **Not validated:** "Not validated" with the button under it. No run-time hint.
- [x] **Validated:**
  - the null badge: "Q above all {d} shuffled networks" / "Q not above the null ({k} of {d})" with `_term(…, "selection.verdict.q_not_above_null")` / "Null Q undefined", each + " ⚠" when `weak`;
  - "Dissolved in most subsamples (re-selected): {n}";
  - two strips labelled R and A: 12 px squares in Cluster order, dark = dissolved in most subsamples, dashed outline = borderline, hatched = not assessable, plain otherwise; each square's `title` is the Cluster label;
  - "median ARI re-selected …, at resolution …" as today;
  - "Open the validation card ↓", scrolling `ps-main` to `ps-validation`, only when the inspected pair equals the card's pair (the default-constraint pair).
- [x] **Catalogue:** the new keys in `i18n/bg/ps_view.py` (and callbacks if a string moves there); "Q above all null replicates" and "Dissolved: {n}" removed.
- [x] Checked in the browser in EN and BG: not validated, each null state, weak, and the card link shown and hidden. Screenshots in Comments.
- [x] App-render tests: the strips (square count and classes) and each badge state; the card link's presence rule.
- [x] The catalogue parity test and the full test suite pass.

## Comments

- 2026-11-05 (agent): Done in 6578269.
- Browser, EN and BG. Not validated: an inspected 13/2 shows "Not validated" with the Validate button under it and no card link ([screenshot](../screenshots/19-inspector-not-validated-1280-en.jpg)). Validated default pair: "Q above all 100 shuffled networks", the strips and the card link ([EN 1600](../screenshots/19-inspector-1600-en.jpg), [BG 1280](../screenshots/19-inspector-1280-bg.jpg)). The link scrolls only the main column, to 8 px above the card, and the URL is unchanged.
- The real runs never reach the other states, so they were produced by editing null records in the scratch demo copy (restored afterwards). Puzzle: 3 nulls set to Q = 1 gave "Q not above the null (3 of 100)" with its help link. RPG: every null beyond_scan gave "Null Q undefined ⚠" and the card's weak warning. Strategy: 60 nulls beyond_scan gave "Q above all 40 shuffled networks ⚠". In BG the last one reads "Q е над всички 40 разбъркани мрежи ⚠".
- Beyond the spec (spec review): the dissolved badge also carries a help link to its glossary entry. Kept.
- Full suite: 635 passed.
