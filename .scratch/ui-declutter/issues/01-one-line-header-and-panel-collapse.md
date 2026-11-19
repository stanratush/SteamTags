# 01: One-line header and collapse buttons on the panels

**What to build:** a header that fits on one line at 1280 px or wider, with the panel toggles moved onto the panels themselves.

**Blocked by:** none

**Status:** done

Spec: [UI Declutter spec](../spec.md): "Header", "Docs". Code: `src/steamstudy/app/layout.py` (`header`, `_language`, `block_styles`, `root_class`), `src/steamstudy/app/ps_view.py`, `callbacks.py`, `assets/workbench.js`, `assets/app.css`.

- [x] The header holds, in order: brand + Build menu · the four mode buttons · Find a tag (in the modes that show it today) · EN | BG, plus `verify-result` and `error-message` at the right. Nothing else.
- [x] At 1280×800 and at 1440×900 the header is one line in every mode, in en and bg (checked in the browser).
- [x] The language switch shows no "Language" word. Its tooltip carries the `header.lang` tip and still opens the help entry.
- [x] The mode button reads "Analysis Report" (bg catalogue entry shortened to match).
- [x] The `panels` and `ps-panels` checklists are gone from the header. Each panel has a collapse button in its title bar: « Controls, » Inspector, ▾ on the Tables tab strip; in Parameter Selection, Controls, Pair Constraints and Inspector likewise.
- [x] A collapsed panel leaves a rail on its edge with the panel's name (rotated for side panels, horizontal for Tables). Clicking the rail reopens it. The button and the rail have accessible names and `aria-expanded`.
- [x] Open/closed state keeps today's storage and effects (root classes, `block_styles`, the first fit filling the canvas after a collapse).
- [x] Graph only sits in the graph toolbar and behaves as today.
- [x] Every new string has a bg entry (`tests/i18n_parity.py` passes).
- [x] User Guide `02-app-controls.md` (en and bg) and `01-getting-started.md` describe the new places; `docs/running-guide.md`'s browser check names the panel collapse buttons.
- [x] Tests (`tests/test_layout.py`, `tests/test_app.py`, `tests/test_ps_app.py`): the header's children; the collapse buttons and rails exist per mode; collapsing and reopening each panel gives today's root classes and block styles.

## Comments

**2026-11-18, implementation.** New `app/panels.py`: the collapse buttons and rails (pattern-matching id `panel-btn`), and `toggled`. The `panels` and `ps-panels` checklists are still the state, hidden in a `hidden` div; `callbacks.toggle_panel` writes them, so `arrange`, `inspector_form` and `psPanels` are unchanged. The language `?` keeps the id `lang-term`, its tooltip, its help target and "Language" as its aria-label. Full suite: 972 passed.

Checked in the browser: one line at 1280×800 (en and bg, Workbench) and at 1440×900 (en Workbench, bg Parameter Selection). All six panels collapse and reopen from their rails, and the graph and heatmap refit. Medium form (1100 px): « is the pill bar's last item, its rail is a bar under the header, and the Inspector has neither a button nor a rail (it floats).

Decided in passing, beyond the spec: below 1280 px the header wraps again (bg overflowed by 36 px at 1100 with wrapping off); the Build name is ellipsized at 220 px so Find a tag keeps room; the bg mode label is „Аналитичен доклад“ in quotes, noted in `docs/i18n/bg-terms.md`. At 1280×800 all four modes in en and bg give a one-row header, 47 px tall (42 px in Cluster Comparison, which has no search), with no overflow.

