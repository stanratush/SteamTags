# 02: Open exports by Build identity

**What to build:** an exported Network State made on one computer opens on another that has the same Build in a different place (another clone, or an App Bundle). The Build is found by identity, not by the absolute path recorded in the export.

**Blocked by:** none

**Status:** done

Spec: [App Bundle spec](../spec.md): "App behaviour changes".

Facts found while grilling: `open_export` in `src/steamstudy/app/export.py` uses the export's absolute `build_path` unless a `build_path` argument is passed, then compares `build_json_hash` of the loaded Build with the copy in the export.

- [x] Opening an export looks for its Build among the Builds available to the running app (the `builds/` tree under the app's `--root`), matching `build_id` and the `build.json` hash; the recorded `build_path` is no longer used to locate it.
- [x] Exports still record `build_path`, described as informational in the schema/guide.
- [x] An export whose Build is not available is refused with a message naming the Build id it needs (and its Snapshot id).
- [x] A Build with the same `build_id` but a different `build.json` hash is refused as today.
- [x] Tests: an export made from a Build, opened after the Build folder is copied to a different root (old path deleted), reproduces the same `state_id` and tables; the missing-Build and hash-mismatch cases are refused.

## Comments

**2026-10-06 (implemented):** `export.find_build(builds_root, build_json)` searches `<builds_root>/*/<build_id>/` and keeps the folder whose `build.json` hash equals the export's copy; `open_export(data, builds_root=…)` no longer reads the recorded `build_path`. A missing Build raises `BuildNotFound` naming the Build id and Snapshot id; the same id with another hash is refused as "differs". The app passes the `builds/` folder above the loaded Build (a `builds-root` store); the "Build folder (if it has moved)" box is gone. Exports still record `build_path`, now described as informational in 04-files and 05-citing-and-reproducing.
