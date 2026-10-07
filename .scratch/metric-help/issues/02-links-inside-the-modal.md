# 02: Links inside the help modal

**What to build:** guide links inside the help modal open their target entry in the modal, with ← Back.

**Blocked by:** 01

**Status:** ready-for-agent

Spec: [Metric help spec](../spec.md): "Links inside the modal".

- [ ] `#anchor` and `<chapter>.md#anchor` links open that entry in the modal. A chapter link without an anchor opens the chapter's first section.
- [ ] ← Back walks a stack of opened entries. The stack clears when the modal closes.
- [ ] External links still open in a new tab.
- [ ] Test: every in-guide link the modal can follow points to an existing heading.
- [ ] Checked in the browser: follow "Compare with" links from Modularity Q to the Null-model baseline and back.

## Comments
