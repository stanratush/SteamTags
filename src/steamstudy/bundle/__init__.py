"""Making an App Bundle (ADR 0001): one zip that runs the Tag Network app on another computer with only Python.

`wheels` plans which wheels from `uv.lock` each target needs; `make` stages and zips the bundle;
`start_tag_network` is the stdlib-only launcher copied into every bundle. Nothing here is imported by the app.
"""
