# Bulk translation slicing and review
Type: grilling
Status: open
Blocked by: none

## Question

How does the Bulgarian text get written and reviewed in implementation-sized slices? Uses `grilling` + `domain-modeling`. Works from the [String inventory](01-string-inventory.md), the [Translation mechanism](02-translation-mechanism.md) and the term table from [Bulgarian terminology](03-bulgarian-terminology.md) ([docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md)).

- **Slices**: how the ~500 app strings (by module: `view.py`, `ps_view.py`, `layout.py`, `selection_text.py`, …) and the ~43,600 hand-translated guide words (by guide file) split into issues of one agent session each, and where the new text of features 2–4 goes (the last slice, or each feature's own issues).
- **Strictness**: when the completeness checks (catalogue entries, guide headings) turn strict. At the last slice, or per module or file as each one is done.
- **Visibility**: whether the EN | BG switch stays hidden or marked as a preview until completeness passes, given that missing entries fall back to English at runtime.
- **Review**: how the researcher reviews (per slice or once at the end, in the app or in the Markdown files), and how corrections flow back into the table and the text.
