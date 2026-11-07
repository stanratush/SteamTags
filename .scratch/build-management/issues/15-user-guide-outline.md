# What does the User Guide cover for the Build menu and Import Builds?
Type: prototype
Status: open
Blocked by: 14

## Question

The User Guide (`docs/user-guide/`, with its `bg/` translation under ADR 0003) has no section for making Builds in the app or for opening imported data. It says "Top-100" 33 times, 20 of them in the metric reference, and its column index (appendix B) is generated from `export/schema.py`, which now has Import variants ([export schema](13-export-schema.md)).

Make a rough outline to react to, and decide:
- which pages gain sections for the Build menu (the steps of a draft, Review, the running-Build strip, switching, Manage Builds) and for Import Builds (the Import file format, what is hidden, the "Game means item, Tag means attribute" note);
- how the Top-100 → Top-N rename sweeps the guide and the bg catalogue, following the glossary decided in [the Top-N glossary ticket](14-top-n-glossary.md);
- what the Running Guide gains for `steamstudy import` and `snapshot lighten`;
- how appendix B shows the Import variants.

The outline is the decision; writing the full text is implementation.
