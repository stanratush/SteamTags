# 14: Straight fixes: the heatmap keeps 460 px, and `gamma_step` must be a multiple of 0.01

**What to build:** two independent straight fixes. The Parameter Selection heatmap no longer shrinks when the main column overflows (review item 1). `config.py` refuses a `gamma_step` that `champ.scan_gammas` would silently turn into an uneven grid. Neither changes a stored result or a version.

**Blocked by:** none

**Status:** ready-for-agent

Spec: [Validation review spec](../spec.md): "Heatmap", "Configuration guard", "Tests". Sources: [Verified review](../research/01-verified-review.md) item 1, [Should the default γ step be finer than 0.05?](12-default-gamma-step.md).

- [ ] **Heatmap:** in `app/assets/app.css`, `#ps-heatmap{flex:0 0 460px}` and `flex-shrink:0` on every direct child of `.ps-main`. The inline `height: 460px` in `ps_view.mode_layout` may stay or go, but the comment says why the heatmap holds its height.
- [ ] Reproduce the collapse in the browser before the fix (a validated pair with a long card at wide 1280), then confirm the heatmap keeps 460 px and the column scrolls. Screenshot both in Comments.
- [ ] A layout test asserts the `flex-shrink` rule on `#ps-heatmap`, if the existing CSS tests can read it; otherwise Comments say why not.
- [ ] **Guard:** `config.py` raises `ConfigError` ("`[parameter_selection].gamma_step`: must be a whole multiple of 0.01") when `round(gamma_step * 100)` differs from `gamma_step * 100` beyond float tolerance. The default 0.05 and every stored setting pass.
- [ ] Test: `gamma_step = 0.025 → ConfigError`; 0.05 and 0.1 load.
- [ ] The full test suite passes.
