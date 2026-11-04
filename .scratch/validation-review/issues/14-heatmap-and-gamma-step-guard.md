# 14: Straight fixes: the heatmap keeps 460 px, and `gamma_step` must be a multiple of 0.01

**What to build:** two independent straight fixes. The Parameter Selection heatmap no longer shrinks when the main column overflows (review item 1). `config.py` refuses a `gamma_step` that `champ.scan_gammas` would silently turn into an uneven grid. Neither changes a stored result or a version.

**Blocked by:** none

**Status:** done

Spec: [Validation review spec](../spec.md): "Heatmap", "Configuration guard", "Tests". Sources: [Verified review](../research/01-verified-review.md) item 1, [Should the default γ step be finer than 0.05?](12-default-gamma-step.md).

- [x] **Heatmap:** in `app/assets/app.css`, `#ps-heatmap{flex:0 0 460px}` and `flex-shrink:0` on every direct child of `.ps-main`. The inline `height: 460px` in `ps_view.mode_layout` may stay or go, but the comment says why the heatmap holds its height.
- [x] Reproduce the collapse in the browser before the fix (a validated pair with a long card at wide 1280), then confirm the heatmap keeps 460 px and the column scrolls. Screenshot both in Comments.
- [x] A layout test asserts the `flex-shrink` rule on `#ps-heatmap`, if the existing CSS tests can read it; otherwise Comments say why not.
- [x] **Guard:** `config.py` raises `ConfigError` ("`[parameter_selection].gamma_step`: must be a whole multiple of 0.01") when `round(gamma_step * 100)` differs from `gamma_step * 100` beyond float tolerance. The default 0.05 and every stored setting pass.
- [x] Test: `gamma_step = 0.025 → ConfigError`; 0.05 and 0.1 load.
- [x] The full test suite passes.

## Comments

- 2026-11-05 (agent): Done in 55895a9. `.ps-main>*{flex-shrink:0}` and `#ps-heatmap{flex:0 0 460px}` in app.css; the `mode_layout` comment says why the height holds. The guard rejects 0.025 and loads 0.05, 0.1, 0.01 and 0.07 (`tests/test_config.py`).
- Layout test: `test_the_heatmap_keeps_its_height_when_the_main_column_overflows` reads app.css.
- Browser, wide 1280 px, validated Overall 17/2 (card 804 px). The fix was already in, so the before state was reproduced by injecting the pre-fix rules (children allowed to shrink). The heatmap container then measured 0 px right after layout, with the plot spilling out of it: [pre-fix rules](../screenshots/14-heatmap-pre-fix-rules-1280-en.jpg). Plotly's own SVG then held it at 460 px once it re-rendered, so the collapse depends on render timing. With the fix it is 460 px from the start and the main column scrolls (scrollHeight 1290 in a 704 px column): [fixed](../screenshots/14-heatmap-fixed-1280-en.jpg).
- Full suite: 635 passed.
