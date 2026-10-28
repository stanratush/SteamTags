"""The strictness ratchet of the Bulgarian translation (spec: .scratch/bilingual-cluster-views/spec.md,
"Strictness ratchet").

Each bulk-translation slice adds its own entries. From then on a missing or orphaned entry inside them fails;
outside them a missing Bulgarian entry falls back to English at runtime. G10 (issue 38) deletes this file, and
completeness is then checked everywhere. No App Bundle is released while this file exists.
"""

# Catalogue areas (`steamstudy.i18n.AREAS`) whose Bulgarian is complete.
CATALOGUE_DONE: set[str] = {"layout", "callbacks", "refusals", "ui_words", "schema_tips"}

# Bulgarian guide files (`03-metric-reference.md`) or `##` sections of a file (`03-metric-reference.md#feature-analysis`)
# that are complete.
GUIDE_DONE: set[str] = set()
