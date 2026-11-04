# 22: Rerun the three sensitivity studies on the new Build

**What to build:** once the coming Build exists and issues 14–21 are done, rerun the mixing, clamp-bracket and scan-step scripts on it by hand, apply the pre-set reopen rule, and update the guide's quoted figures in both languages. Nothing runs at bundle time.

**Blocked by:** 14, 15, 16, 17, 18, 19, 20, 21, and the new Build

**Status:** ready-for-agent

Spec: [Validation review spec](../spec.md): "New-Build rerun". Scripts and rerun commands: [08-mixing-check](../prototypes/08-mixing-check/README.md), [09-clamp-bracket](../prototypes/09-clamp-bracket/README.md), [10-scan-step](../prototypes/10-scan-step/README.md). Sources: [Which sensitivity checks run…?](05-sensitivity-checks-and-scope.md), [Should the default γ step be finer than 0.05?](12-default-gamma-step.md), [How are versions, reruns and tests staged?](07-versioning-reruns-and-tests.md).

- [ ] Validate the new Build's default-constraint pairs in the app (`ps-validation-2`), so the scripts have stored validations to pair with. List the pairs in Comments.
- [ ] Run the three scripts with the Build path and those pairs (about 75 min in all). If a script needs a change for the new records (for example the cache key length or `ps-validation-2` fields), make it and say so. Commit results beside the old ones, dated.
- [ ] **Reopen rule** (scan-step study, at step 0.01): the default γ step reopens if any observed Selected Partition changes, an observed width crosses the null median, or k/K **falls** by 0.10 or more. If it fires, Comments say so and a fresh question goes to the Automatic Parameter Selection side; nothing else in this issue waits on it.
- [ ] **Mixing:** if any pair has not plateaued by 10 trades per game, Comments say so and a follow-up opens on `TRADES_PER_GAME`.
- [ ] **Guide quotes** (en and bg, `03-metric-reference.md` and `bg/`): the figures and the Build date in the quotes from tickets 08, 09 and 10, and the 0.58–0.70 Perturbation Share range, from the new results; also the Overall 17/2 example figures if that pair's stored figures moved.
- [ ] The guide tests and the full test suite pass.
