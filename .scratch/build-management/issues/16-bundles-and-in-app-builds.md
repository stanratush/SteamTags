# How does the bundle maker pick in-app Builds, and what does a Bundle show of their names and lineage?
Type: grilling
Status: open
Blocked by:

## Question

`steamstudy bundle` always ships `latest` plus each `--build <build_id>`. It names the zip `tag-network-<build_id>-<targets>.zip` and runs Parameter Selection for every Build it carries (`bundle/make.py`, [releasing guide](../../../docs/releasing-an-app-bundle.md)). Builds made in the app have a required name, a description and a parent ([Build identity](07-build-identity-and-lifecycle.md)). Delete moves `latest`. An Import Build lives under `builds/<import_id>/` and is self-contained ([export schema](13-export-schema.md)). A Bundle gets the Build tree for switching only ([Build menu](12-build-menu.md)).

Decide:
- whether `latest` stays the implicit default once Builds are made often in the app, or a Bundle names its Builds explicitly, and whether `--build` accepts a Build's name as well as its id;
- whether Import Builds can be bundled (the Import folder is not shipped), and with what checks;
- whether the zip name and `bundle.json` carry the Build's name, and how the bundled tree shows a parent that is not in the Bundle;
- whether the bundle maker refuses or warns about a Build with a failed draft, a test Snapshot, or a lightweight-only source.
